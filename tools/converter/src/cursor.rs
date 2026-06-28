//! Windows cursor encoders: `.cur` (static) and `.ani` (animated).
//!
//! `.cur` is the ICO container with image type `2`; the per-image "planes"/
//! "bitcount" fields are reused to store the hotspot (x, y). Image payloads are
//! classic 32bpp bottom-up BMP (BITMAPINFOHEADER + BGRA XOR bitmap + 1bpp AND
//! mask), which every Windows version understands.
//!
//! `.ani` is a RIFF `ACON` file: an `anih` header, an optional `rate` chunk for
//! per-frame timing, and a `LIST`/`fram` group of `icon` chunks, each a full
//! `.cur` file (the `AF_ICON` attribute tells Windows the frames carry hotspots).

use crate::cli::{AniArgs, CurArgs};
use crate::svg;
use crate::util;
use anyhow::{Context, Result};
use image::codecs::gif::GifDecoder;
use image::{AnimationDecoder, RgbaImage};
use std::fs::File;
use std::io::BufReader;
use std::path::Path;

/// Render any supported input to a square RGBA image at `size` px.
fn load_rgba_square(path: &Path, size: u32) -> Result<RgbaImage> {
    if util::is_svg(path) {
        let pixmap = svg::render_to_pixmap(path, Some(size), Some(size), None)?;
        Ok(svg::pixmap_to_dynamic(&pixmap).to_rgba8())
    } else {
        let img = image::open(path).with_context(|| format!("decoding {}", path.display()))?;
        Ok(img
            .resize_exact(size, size, image::imageops::FilterType::Lanczos3)
            .to_rgba8())
    }
}

// ---- little-endian writers -------------------------------------------------

fn push_u16(buf: &mut Vec<u8>, v: u16) {
    buf.extend_from_slice(&v.to_le_bytes());
}
fn push_u32(buf: &mut Vec<u8>, v: u32) {
    buf.extend_from_slice(&v.to_le_bytes());
}

/// Encode one image's BMP payload (header + XOR BGRA + AND mask), bottom-up.
fn bmp_payload(img: &RgbaImage) -> Vec<u8> {
    let (w, h) = (img.width(), img.height());
    let mut out = Vec::new();

    // BITMAPINFOHEADER (40 bytes). Height is doubled (XOR + AND).
    push_u32(&mut out, 40); // biSize
    push_u32(&mut out, w); // biWidth
    push_u32(&mut out, h * 2); // biHeight (XOR + AND)
    push_u16(&mut out, 1); // biPlanes
    push_u16(&mut out, 32); // biBitCount
    push_u32(&mut out, 0); // biCompression = BI_RGB
    push_u32(&mut out, 0); // biSizeImage
    push_u32(&mut out, 0); // biXPelsPerMeter
    push_u32(&mut out, 0); // biYPelsPerMeter
    push_u32(&mut out, 0); // biClrUsed
    push_u32(&mut out, 0); // biClrImportant

    // XOR bitmap: 32bpp BGRA, rows bottom-to-top.
    for y in (0..h).rev() {
        for x in 0..w {
            let p = img.get_pixel(x, y).0;
            out.push(p[2]); // B
            out.push(p[1]); // G
            out.push(p[0]); // R
            out.push(p[3]); // A
        }
    }

    // AND mask: 1bpp, bottom-to-top, rows padded to 32-bit. 1 = transparent.
    let row_bytes = (w.div_ceil(32) * 4) as usize;
    for y in (0..h).rev() {
        let mut row = vec![0u8; row_bytes];
        for x in 0..w {
            if img.get_pixel(x, y).0[3] < 128 {
                row[(x / 8) as usize] |= 0x80 >> (x % 8);
            }
        }
        out.extend_from_slice(&row);
    }
    out
}

/// Build a `.cur` file from one or more (image, hotspot) entries.
pub fn encode_cur(entries: &[(RgbaImage, u16, u16)]) -> Vec<u8> {
    let count = entries.len() as u16;
    let mut out = Vec::new();

    // ICONDIR
    push_u16(&mut out, 0); // reserved
    push_u16(&mut out, 2); // type = 2 (cursor)
    push_u16(&mut out, count);

    // Pre-render payloads to know sizes/offsets.
    let payloads: Vec<Vec<u8>> = entries.iter().map(|(img, _, _)| bmp_payload(img)).collect();
    let mut offset = 6 + 16 * count as u32; // after dir + all entries

    for (i, (img, hx, hy)) in entries.iter().enumerate() {
        let (w, h) = (img.width(), img.height());
        out.push(if w >= 256 { 0 } else { w as u8 }); // bWidth (0 => 256)
        out.push(if h >= 256 { 0 } else { h as u8 }); // bHeight
        out.push(0); // bColorCount
        out.push(0); // bReserved
        push_u16(&mut out, *hx); // hotspot X (planes field)
        push_u16(&mut out, *hy); // hotspot Y (bitcount field)
        let len = payloads[i].len() as u32;
        push_u32(&mut out, len); // dwBytesInRes
        push_u32(&mut out, offset); // dwImageOffset
        offset += len;
    }
    for p in &payloads {
        out.extend_from_slice(p);
    }
    out
}

// ---- RIFF helpers for .ani -------------------------------------------------

/// Append a RIFF chunk (`id` + size + data + pad byte if odd length).
fn push_chunk(buf: &mut Vec<u8>, id: &[u8; 4], data: &[u8]) {
    buf.extend_from_slice(id);
    push_u32(buf, data.len() as u32);
    buf.extend_from_slice(data);
    if data.len() % 2 == 1 {
        buf.push(0); // word alignment
    }
}

/// Build an `.ani` file from per-frame `.cur` blobs and per-frame delays (jiffies, 1/60s).
pub fn encode_ani(frames: &[Vec<u8>], rates_jiffies: &[u32], w: u32, h: u32) -> Vec<u8> {
    let n = frames.len() as u32;

    // anih (ANIHEADER, 36 bytes)
    let mut anih = Vec::new();
    push_u32(&mut anih, 36); // cbSize
    push_u32(&mut anih, n); // nFrames
    push_u32(&mut anih, n); // nSteps
    push_u32(&mut anih, w); // iWidth
    push_u32(&mut anih, h); // iHeight
    push_u32(&mut anih, 0); // iBitCount
    push_u32(&mut anih, 1); // nPlanes
    push_u32(&mut anih, *rates_jiffies.first().unwrap_or(&10)); // iDispRate
    push_u32(&mut anih, 1); // bfAttributes: bit0 AF_ICON (frames are .cur)

    // rate chunk: one u32 per frame
    let mut rate = Vec::new();
    for r in rates_jiffies {
        push_u32(&mut rate, (*r).max(1));
    }

    // LIST 'fram' of 'icon' chunks
    let mut fram = Vec::new();
    fram.extend_from_slice(b"fram");
    for f in frames {
        push_chunk(&mut fram, b"icon", f);
    }

    // Assemble RIFF body
    let mut body = Vec::new();
    body.extend_from_slice(b"ACON");
    push_chunk(&mut body, b"anih", &anih);
    push_chunk(&mut body, b"rate", &rate);
    push_chunk(&mut body, b"LIST", &fram);

    let mut out = Vec::new();
    out.extend_from_slice(b"RIFF");
    push_u32(&mut out, body.len() as u32);
    out.extend_from_slice(&body);
    out
}

// ---- command entry points --------------------------------------------------

pub fn cur(a: &CurArgs) -> Result<()> {
    anyhow::ensure!(!a.sizes.is_empty(), "provide at least one --sizes value");
    // Hotspot is given for the first (nominal) size; scale it to each variant.
    let base = a.sizes[0] as f32;
    let mut entries = Vec::new();
    for &s in &a.sizes {
        let img = load_rgba_square(&a.input, s)?;
        let k = s as f32 / base;
        let hx = ((a.hotspot_x as f32) * k).round() as u16;
        let hy = ((a.hotspot_y as f32) * k).round() as u16;
        entries.push((img, hx.min((s - 1) as u16), hy.min((s - 1) as u16)));
    }
    let out = a
        .output
        .clone()
        .unwrap_or_else(|| util::derive_output(&a.input, "", Some("cur")));
    util::ensure_parent(&out)?;
    std::fs::write(&out, encode_cur(&entries))
        .with_context(|| format!("writing {}", out.display()))?;
    println!(
        "cur {} -> {} ({} size(s), hotspot {},{})",
        a.input.display(),
        out.display(),
        a.sizes.len(),
        a.hotspot_x,
        a.hotspot_y
    );
    Ok(())
}

pub fn ani(a: &AniArgs) -> Result<()> {
    anyhow::ensure!(
        crate::raster::is_gif(&a.input),
        "ani input must be an animated GIF"
    );
    let decoder = GifDecoder::new(BufReader::new(File::open(&a.input)?))?;
    let gif_frames = decoder.into_frames().collect_frames()?;
    anyhow::ensure!(!gif_frames.is_empty(), "GIF has no frames");

    let size = a.size;
    let hx = a.hotspot_x.min(size.saturating_sub(1)) as u16;
    let hy = a.hotspot_y.min(size.saturating_sub(1)) as u16;

    let mut cur_frames = Vec::with_capacity(gif_frames.len());
    let mut rates = Vec::with_capacity(gif_frames.len());
    for frame in &gif_frames {
        let resized = image::imageops::resize(
            frame.buffer(),
            size,
            size,
            image::imageops::FilterType::Lanczos3,
        );
        cur_frames.push(encode_cur(&[(resized, hx, hy)]));

        let jiffies = if let Some(fps) = a.fps {
            (60.0 / fps.max(1) as f32).round() as u32
        } else {
            // Delay is (numer/denom) milliseconds; convert ms -> jiffies (1/60s).
            let (n, d) = frame.delay().numer_denom_ms();
            let ms = if d == 0 { 100.0 } else { n as f32 / d as f32 };
            (ms * 60.0 / 1000.0).round() as u32
        };
        rates.push(jiffies.max(1));
    }

    let out = a
        .output
        .clone()
        .unwrap_or_else(|| util::derive_output(&a.input, "", Some("ani")));
    util::ensure_parent(&out)?;
    std::fs::write(&out, encode_ani(&cur_frames, &rates, size, size))
        .with_context(|| format!("writing {}", out.display()))?;
    println!(
        "ani {} -> {} ({} frames @ {}px, hotspot {},{})",
        a.input.display(),
        out.display(),
        cur_frames.len(),
        size,
        a.hotspot_x,
        a.hotspot_y
    );
    Ok(())
}
