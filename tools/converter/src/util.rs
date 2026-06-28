//! Shared helpers.

use anyhow::{Context, Result};
use std::path::{Path, PathBuf};

/// Compute a target (w, h) honouring aspect ratio unless `exact`.
pub fn target_dims(
    src_w: u32,
    src_h: u32,
    width: Option<u32>,
    height: Option<u32>,
    scale: Option<f32>,
    exact: bool,
) -> Result<(u32, u32)> {
    if let Some(s) = scale {
        anyhow::ensure!(s > 0.0, "scale must be positive");
        let w = ((src_w as f32) * s).round().max(1.0) as u32;
        let h = ((src_h as f32) * s).round().max(1.0) as u32;
        return Ok((w, h));
    }
    match (width, height) {
        (Some(w), Some(h)) if exact => Ok((w.max(1), h.max(1))),
        (Some(w), Some(h)) => {
            // Fit inside the box preserving aspect ratio.
            let r = (w as f32 / src_w as f32).min(h as f32 / src_h as f32);
            Ok((
                ((src_w as f32 * r).round() as u32).max(1),
                ((src_h as f32 * r).round() as u32).max(1),
            ))
        }
        (Some(w), None) => {
            let r = w as f32 / src_w as f32;
            Ok((w.max(1), ((src_h as f32 * r).round() as u32).max(1)))
        }
        (None, Some(h)) => {
            let r = h as f32 / src_h as f32;
            Ok((((src_w as f32 * r).round() as u32).max(1), h.max(1)))
        }
        (None, None) => anyhow::bail!("specify --width, --height, or --scale"),
    }
}

/// Derive an output path next to `input` with a `_suffix` and optional new ext.
pub fn derive_output(input: &Path, suffix: &str, new_ext: Option<&str>) -> PathBuf {
    let stem = input.file_stem().and_then(|s| s.to_str()).unwrap_or("out");
    let ext = new_ext
        .map(|e| e.to_string())
        .or_else(|| {
            input
                .extension()
                .and_then(|e| e.to_str())
                .map(|s| s.to_string())
        })
        .unwrap_or_else(|| "png".to_string());
    let file = if suffix.is_empty() {
        format!("{stem}.{ext}")
    } else {
        format!("{stem}_{suffix}.{ext}")
    };
    input.with_file_name(file)
}

/// Ensure the parent directory of `path` exists.
pub fn ensure_parent(path: &Path) -> Result<()> {
    if let Some(parent) = path.parent() {
        if !parent.as_os_str().is_empty() {
            std::fs::create_dir_all(parent)
                .with_context(|| format!("creating directory {}", parent.display()))?;
        }
    }
    Ok(())
}

/// True if a path looks like an SVG by extension.
pub fn is_svg(path: &Path) -> bool {
    path.extension()
        .and_then(|e| e.to_str())
        .map(|e| e.eq_ignore_ascii_case("svg"))
        .unwrap_or(false)
}
