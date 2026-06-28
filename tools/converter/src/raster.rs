//! Raster image operations: resize, convert, multi-size, info.

use crate::cli::{ConvertArgs, Filter, InfoArgs, OutFormat, ResizeArgs, SizesArgs};
use crate::svg;
use crate::util;
use anyhow::{Context, Result};
use image::codecs::gif::{GifDecoder, GifEncoder, Repeat};
use image::{AnimationDecoder, DynamicImage, Frame, ImageReader};
use std::fs::File;
use std::io::{BufReader, BufWriter};
use std::path::Path;

fn is_gif(path: &Path) -> bool {
    path.extension()
        .and_then(|e| e.to_str())
        .map(|e| e.eq_ignore_ascii_case("gif"))
        .unwrap_or(false)
}

/// Read the intrinsic dimensions of a raster file without full decode.
fn read_dims(path: &Path) -> Result<(u32, u32)> {
    let reader = ImageReader::open(path)
        .with_context(|| format!("opening {}", path.display()))?
        .with_guessed_format()?;
    reader
        .into_dimensions()
        .with_context(|| format!("reading dimensions of {}", path.display()))
}

pub fn resize(a: &ResizeArgs) -> Result<()> {
    // Animation-aware path for multi-frame GIFs.
    if is_gif(&a.input) {
        let (w, h) = read_dims(&a.input)?;
        let (tw, th) = util::target_dims(w, h, a.width, a.height, a.scale, a.exact)?;
        let out = a
            .output
            .clone()
            .unwrap_or_else(|| util::derive_output(&a.input, &format!("{tw}x{th}"), Some("gif")));
        if resize_gif(&a.input, &out, tw, th, a.filter)? {
            println!(
                "resized (animated) {} -> {} ({tw}x{th})",
                a.input.display(),
                out.display()
            );
            return Ok(());
        }
        // Fell through: single-frame gif, handled below as a still image.
    }

    let img = image::open(&a.input).with_context(|| format!("decoding {}", a.input.display()))?;
    let (tw, th) = util::target_dims(
        img.width(),
        img.height(),
        a.width,
        a.height,
        a.scale,
        a.exact,
    )?;
    let resized = if a.exact && a.width.is_some() && a.height.is_some() {
        img.resize_exact(tw, th, a.filter.to_image())
    } else {
        img.resize(tw, th, a.filter.to_image())
    };
    let out = a.output.clone().unwrap_or_else(|| {
        util::derive_output(
            &a.input,
            &format!("{}x{}", resized.width(), resized.height()),
            None,
        )
    });
    util::ensure_parent(&out)?;
    resized
        .save(&out)
        .with_context(|| format!("saving {}", out.display()))?;
    println!(
        "resized {} -> {} ({}x{})",
        a.input.display(),
        out.display(),
        resized.width(),
        resized.height()
    );
    Ok(())
}

/// Resize every frame of an animated GIF. Returns false if the GIF has a single frame.
fn resize_gif(input: &Path, output: &Path, w: u32, h: u32, filter: Filter) -> Result<bool> {
    let decoder = GifDecoder::new(BufReader::new(File::open(input)?))?;
    let frames = decoder.into_frames().collect_frames()?;
    if frames.len() <= 1 {
        return Ok(false);
    }
    util::ensure_parent(output)?;
    let file = BufWriter::new(File::create(output)?);
    let mut encoder = GifEncoder::new(file);
    encoder.set_repeat(Repeat::Infinite)?;
    for frame in frames {
        let delay = frame.delay();
        let buf = image::imageops::resize(frame.buffer(), w, h, filter.to_image());
        encoder.encode_frame(Frame::from_parts(buf, 0, 0, delay))?;
    }
    Ok(true)
}

pub fn convert(a: &ConvertArgs) -> Result<()> {
    let img = image::open(&a.input).with_context(|| format!("decoding {}", a.input.display()))?;
    let out = a
        .output
        .clone()
        .unwrap_or_else(|| util::derive_output(&a.input, "", Some(a.to.ext())));
    util::ensure_parent(&out)?;
    encode(&img, &out, a.to, a.quality)?;
    println!(
        "converted {} -> {} ({})",
        a.input.display(),
        out.display(),
        a.to.ext()
    );
    Ok(())
}

/// Encode a DynamicImage to a specific format, honouring quality where supported.
pub fn encode(img: &DynamicImage, out: &Path, fmt: OutFormat, quality: u8) -> Result<()> {
    use image::codecs::jpeg::JpegEncoder;
    util::ensure_parent(out)?;
    match fmt {
        OutFormat::Jpeg => {
            let file = BufWriter::new(File::create(out)?);
            let mut enc = JpegEncoder::new_with_quality(file, quality.clamp(1, 100));
            // JPEG has no alpha; flatten to RGB.
            enc.encode_image(&DynamicImage::ImageRgb8(img.to_rgb8()))?;
        }
        OutFormat::Ico => {
            // ICO favours small square sizes; downscale if larger than 256.
            let i = if img.width() > 256 || img.height() > 256 {
                img.resize(256, 256, image::imageops::FilterType::Lanczos3)
            } else {
                img.clone()
            };
            i.save_with_format(out, image::ImageFormat::Ico)?;
        }
        OutFormat::Png => img.save_with_format(out, image::ImageFormat::Png)?,
        OutFormat::Webp => img.save_with_format(out, image::ImageFormat::WebP)?,
        OutFormat::Gif => img.save_with_format(out, image::ImageFormat::Gif)?,
        OutFormat::Bmp => img.save_with_format(out, image::ImageFormat::Bmp)?,
        OutFormat::Tiff => img.save_with_format(out, image::ImageFormat::Tiff)?,
    }
    Ok(())
}

pub fn sizes(a: &SizesArgs) -> Result<()> {
    anyhow::ensure!(!a.sizes.is_empty(), "provide at least one --sizes value");
    let stem = a
        .input
        .file_stem()
        .and_then(|s| s.to_str())
        .unwrap_or("asset")
        .to_string();
    std::fs::create_dir_all(&a.outdir)?;

    for &s in &a.sizes {
        let out = a.outdir.join(format!("{stem}_{s}.{}", a.to.ext()));
        if util::is_svg(&a.input) {
            // Render SVG crisply at each size rather than upscaling a raster.
            let pixmap = svg::render_to_pixmap(&a.input, Some(s), Some(s), None)?;
            let img = svg::pixmap_to_dynamic(&pixmap);
            encode(&img, &out, a.to, 90)?;
        } else {
            let img =
                image::open(&a.input).with_context(|| format!("decoding {}", a.input.display()))?;
            let scaled = img.resize(s, s, a.filter.to_image());
            encode(&scaled, &out, a.to, 90)?;
        }
        println!("  wrote {}", out.display());
    }
    println!("emitted {} sizes from {}", a.sizes.len(), a.input.display());
    Ok(())
}

pub fn info(a: &InfoArgs) -> Result<()> {
    let path = &a.input;
    if util::is_svg(path) {
        let (w, h) = svg::intrinsic_size(path)?;
        println!("{}", path.display());
        println!("  type:   SVG (vector)");
        println!("  size:   {:.0}x{:.0} (intrinsic)", w, h);
        return Ok(());
    }
    let reader = ImageReader::open(path)?.with_guessed_format()?;
    let format = reader.format();
    let (w, h) = reader.into_dimensions()?;
    let bytes = std::fs::metadata(path)?.len();
    println!("{}", path.display());
    println!("  format: {:?}", format);
    println!("  size:   {w}x{h}");
    println!("  bytes:  {bytes}");
    if is_gif(path) {
        if let Ok(dec) = GifDecoder::new(BufReader::new(File::open(path)?)) {
            let frames = dec.into_frames().count();
            println!("  frames: {frames}");
        }
    }
    Ok(())
}
