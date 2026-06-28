//! Catalog-manifest-driven batch processing.
//!
//! The manifest (default `catalog/manifest.json`) declares every source asset
//! and the derived outputs that should be generated into `dist/`. This keeps the
//! source tree authoritative and the generated tree reproducible.

use crate::cli::{BatchArgs, Filter, OutFormat};
use crate::raster;
use crate::svg;
use crate::util;
use anyhow::{Context, Result};
use rayon::prelude::*;
use serde::Deserialize;
use std::path::{Path, PathBuf};

#[derive(Debug, Deserialize)]
pub struct Manifest {
    #[serde(default = "default_version")]
    pub version: u32,
    #[serde(default)]
    pub defaults: Defaults,
    pub assets: Vec<Asset>,
}

fn default_version() -> u32 {
    1
}

#[derive(Debug, Deserialize, Default)]
pub struct Defaults {
    #[serde(default)]
    pub outdir: Option<String>,
}

#[derive(Debug, Deserialize)]
pub struct Asset {
    pub source: PathBuf,
    #[serde(default)]
    pub category: Option<String>,
    #[serde(default)]
    pub tags: Vec<String>,
    #[serde(default)]
    pub license: Option<String>,
    #[serde(default)]
    pub outputs: Vec<Output>,
}

#[derive(Debug, Deserialize)]
#[serde(tag = "op", rename_all = "lowercase")]
pub enum Output {
    Resize {
        #[serde(default)]
        width: Option<u32>,
        #[serde(default)]
        height: Option<u32>,
        #[serde(default)]
        scale: Option<f32>,
        #[serde(default)]
        exact: bool,
        #[serde(default)]
        format: Option<OutFormat>,
        outdir: Option<String>,
    },
    Convert {
        format: OutFormat,
        #[serde(default = "default_quality")]
        quality: u8,
        outdir: Option<String>,
    },
    Rasterize {
        #[serde(default)]
        width: Option<u32>,
        #[serde(default)]
        height: Option<u32>,
        #[serde(default)]
        scale: Option<f32>,
        outdir: Option<String>,
    },
    Sizes {
        sizes: Vec<u32>,
        #[serde(default = "default_png")]
        format: OutFormat,
        outdir: Option<String>,
    },
}

fn default_quality() -> u8 {
    90
}
fn default_png() -> OutFormat {
    OutFormat::Png
}

pub fn run_batch(a: &BatchArgs) -> Result<()> {
    let text = std::fs::read_to_string(&a.manifest)
        .with_context(|| format!("reading manifest {}", a.manifest.display()))?;
    let manifest: Manifest =
        serde_json::from_str(&text).with_context(|| format!("parsing {}", a.manifest.display()))?;
    anyhow::ensure!(
        manifest.version == 1,
        "unsupported manifest version {}",
        manifest.version
    );

    let base_outdir = manifest
        .defaults
        .outdir
        .clone()
        .unwrap_or_else(|| "dist".into());

    let total: usize = manifest.assets.iter().map(|x| x.outputs.len().max(1)).sum();
    println!(
        "manifest: {} assets, {} outputs{}",
        manifest.assets.len(),
        total,
        if a.dry_run { " (dry-run)" } else { "" }
    );

    let results: Vec<Result<()>> = manifest
        .assets
        .par_iter()
        .map(|asset| process_asset(asset, &base_outdir, a.dry_run))
        .collect();

    let mut errors = 0;
    for r in results {
        if let Err(e) = r {
            eprintln!("error: {e:#}");
            errors += 1;
        }
    }
    anyhow::ensure!(errors == 0, "{errors} asset(s) failed");
    println!("done");
    Ok(())
}

fn process_asset(asset: &Asset, base_outdir: &str, dry_run: bool) -> Result<()> {
    anyhow::ensure!(
        asset.source.exists(),
        "source not found: {}",
        asset.source.display()
    );
    let stem = asset
        .source
        .file_stem()
        .and_then(|s| s.to_str())
        .unwrap_or("asset")
        .to_string();

    // Surface catalog metadata; flag assets that ship without a license.
    let cat = asset.category.as_deref().unwrap_or("uncategorized");
    match &asset.license {
        Some(lic) => println!(
            "• {} [{cat}] license={lic} tags={:?}",
            asset.source.display(),
            asset.tags
        ),
        None => eprintln!(
            "warning: {} [{cat}] has no license declared",
            asset.source.display()
        ),
    }

    for out in &asset.outputs {
        match out {
            Output::Resize {
                width,
                height,
                scale,
                exact,
                format,
                outdir,
            } => {
                let fmt = format.unwrap_or(infer_format(&asset.source));
                let dest_dir = resolve_dir(outdir.as_deref(), base_outdir);
                let dest = dest_dir.join(format!("{stem}.{}", fmt.ext()));
                log_plan("resize", &asset.source, &dest, dry_run);
                if dry_run {
                    continue;
                }
                let img = image::open(&asset.source)?;
                let (tw, th) =
                    util::target_dims(img.width(), img.height(), *width, *height, *scale, *exact)?;
                let scaled = if *exact && width.is_some() && height.is_some() {
                    img.resize_exact(tw, th, Filter::default().to_image())
                } else {
                    img.resize(tw, th, Filter::default().to_image())
                };
                raster::encode(&scaled, &dest, fmt, 90)?;
            }
            Output::Convert {
                format,
                quality,
                outdir,
            } => {
                let dest_dir = resolve_dir(outdir.as_deref(), base_outdir);
                let dest = dest_dir.join(format!("{stem}.{}", format.ext()));
                log_plan("convert", &asset.source, &dest, dry_run);
                if dry_run {
                    continue;
                }
                let img = image::open(&asset.source)?;
                raster::encode(&img, &dest, *format, *quality)?;
            }
            Output::Rasterize {
                width,
                height,
                scale,
                outdir,
            } => {
                let dest_dir = resolve_dir(outdir.as_deref(), base_outdir);
                let dest = dest_dir.join(format!("{stem}.png"));
                log_plan("rasterize", &asset.source, &dest, dry_run);
                if dry_run {
                    continue;
                }
                let pixmap = svg::render_to_pixmap(&asset.source, *width, *height, *scale)?;
                util::ensure_parent(&dest)?;
                std::fs::write(&dest, pixmap.encode_png()?)?;
            }
            Output::Sizes {
                sizes,
                format,
                outdir,
            } => {
                let dest_dir = resolve_dir(outdir.as_deref(), base_outdir);
                for &s in sizes {
                    let dest = dest_dir.join(format!("{stem}_{s}.{}", format.ext()));
                    log_plan("sizes", &asset.source, &dest, dry_run);
                    if dry_run {
                        continue;
                    }
                    let img = if util::is_svg(&asset.source) {
                        svg::pixmap_to_dynamic(&svg::render_to_pixmap(
                            &asset.source,
                            Some(s),
                            Some(s),
                            None,
                        )?)
                    } else {
                        image::open(&asset.source)?.resize(s, s, Filter::default().to_image())
                    };
                    raster::encode(&img, &dest, *format, 90)?;
                }
            }
        }
    }
    Ok(())
}

fn resolve_dir(outdir: Option<&str>, base: &str) -> PathBuf {
    PathBuf::from(outdir.unwrap_or(base))
}

fn infer_format(path: &Path) -> OutFormat {
    match path
        .extension()
        .and_then(|e| e.to_str())
        .map(|s| s.to_ascii_lowercase())
        .as_deref()
    {
        Some("jpg") | Some("jpeg") => OutFormat::Jpeg,
        Some("webp") => OutFormat::Webp,
        Some("gif") => OutFormat::Gif,
        Some("bmp") => OutFormat::Bmp,
        Some("tiff") | Some("tif") => OutFormat::Tiff,
        Some("ico") => OutFormat::Ico,
        _ => OutFormat::Png,
    }
}

fn log_plan(op: &str, src: &Path, dest: &Path, dry_run: bool) {
    let tag = if dry_run { "plan" } else { "make" };
    println!("  [{tag}] {op}: {} -> {}", src.display(), dest.display());
}
