//! SVG rasterization built on resvg / usvg / tiny-skia.

use crate::cli::RasterizeArgs;
use crate::util;
use anyhow::{Context, Result};
use image::{DynamicImage, RgbaImage};
use std::path::Path;

/// Parse an SVG file into a usvg tree.
fn load_tree(path: &Path) -> Result<usvg::Tree> {
    let data = std::fs::read(path).with_context(|| format!("reading {}", path.display()))?;
    let mut opt = usvg::Options::default();
    // Load system fonts so SVGs containing text render with real glyphs.
    opt.fontdb_mut().load_system_fonts();
    usvg::Tree::from_data(&data, &opt).with_context(|| format!("parsing SVG {}", path.display()))
}

/// Intrinsic (viewBox-derived) size of an SVG in pixels.
pub fn intrinsic_size(path: &Path) -> Result<(f32, f32)> {
    let tree = load_tree(path)?;
    let size = tree.size();
    Ok((size.width(), size.height()))
}

/// Render an SVG to a tiny-skia pixmap at the requested dimensions.
///
/// Width/height fall back to the intrinsic size; aspect ratio is preserved
/// when only one of them (or a scale) is supplied.
pub fn render_to_pixmap(
    path: &Path,
    width: Option<u32>,
    height: Option<u32>,
    scale: Option<f32>,
) -> Result<tiny_skia::Pixmap> {
    let tree = load_tree(path)?;
    let size = tree.size();
    let (iw, ih) = (size.width(), size.height());

    let (tw, th) = util::target_dims(
        iw.round().max(1.0) as u32,
        ih.round().max(1.0) as u32,
        width,
        height,
        scale,
        // Exact only when both width and height are explicitly given.
        width.is_some() && height.is_some(),
    )?;

    let mut pixmap = tiny_skia::Pixmap::new(tw, th)
        .context("failed to allocate pixmap (size too large or zero)")?;
    let transform = tiny_skia::Transform::from_scale(tw as f32 / iw, th as f32 / ih);
    resvg::render(&tree, transform, &mut pixmap.as_mut());
    Ok(pixmap)
}

/// Convert a tiny-skia pixmap (premultiplied) into a DynamicImage (straight alpha).
pub fn pixmap_to_dynamic(pixmap: &tiny_skia::Pixmap) -> DynamicImage {
    let (w, h) = (pixmap.width(), pixmap.height());
    let mut img = RgbaImage::new(w, h);
    for (dst, src) in img.pixels_mut().zip(pixmap.pixels().iter()) {
        let c = src.demultiply();
        *dst = image::Rgba([c.red(), c.green(), c.blue(), c.alpha()]);
    }
    DynamicImage::ImageRgba8(img)
}

pub fn rasterize(a: &RasterizeArgs) -> Result<()> {
    let pixmap = render_to_pixmap(&a.input, a.width, a.height, a.scale)?;
    let out = a.output.clone().unwrap_or_else(|| {
        util::derive_output(
            &a.input,
            &format!("{}x{}", pixmap.width(), pixmap.height()),
            Some("png"),
        )
    });
    util::ensure_parent(&out)?;
    let png = pixmap.encode_png().context("encoding PNG")?;
    std::fs::write(&out, png).with_context(|| format!("writing {}", out.display()))?;
    println!(
        "rasterized {} -> {} ({}x{})",
        a.input.display(),
        out.display(),
        pixmap.width(),
        pixmap.height()
    );
    Ok(())
}
