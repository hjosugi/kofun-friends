//! Command-line interface definitions.

use clap::{Args, Parser, Subcommand, ValueEnum};
use serde::Deserialize;
use std::path::PathBuf;

#[derive(Parser, Debug)]
#[command(
    name = "kofun-convert",
    version,
    about = "Native asset converter for the kofun-friends library",
    long_about = None
)]
pub struct Cli {
    #[command(subcommand)]
    pub command: Command,
}

#[derive(Subcommand, Debug)]
pub enum Command {
    /// Resize a raster image (animation-aware for GIF).
    Resize(ResizeArgs),
    /// Convert a raster image between formats.
    Convert(ConvertArgs),
    /// Rasterize an SVG to PNG at a target size.
    Rasterize(RasterizeArgs),
    /// Emit a source at multiple sizes (icon/emoji/cursor sets).
    Sizes(SizesArgs),
    /// Print metadata about an image.
    Info(InfoArgs),
    /// Build a Windows static cursor (.cur) from an SVG/raster.
    Cur(CurArgs),
    /// Build a Windows animated cursor (.ani) from an animated GIF.
    Ani(AniArgs),
    /// Process a directory tree driven by a catalog manifest.
    Batch(BatchArgs),
}

/// Output raster formats supported for encoding.
#[derive(ValueEnum, Clone, Copy, Debug, PartialEq, Eq, Deserialize)]
#[serde(rename_all = "lowercase")]
pub enum OutFormat {
    Png,
    Jpeg,
    Webp,
    Gif,
    Bmp,
    Tiff,
    Ico,
}

impl OutFormat {
    pub fn ext(self) -> &'static str {
        match self {
            OutFormat::Png => "png",
            OutFormat::Jpeg => "jpg",
            OutFormat::Webp => "webp",
            OutFormat::Gif => "gif",
            OutFormat::Bmp => "bmp",
            OutFormat::Tiff => "tiff",
            OutFormat::Ico => "ico",
        }
    }
}

/// Resampling filter used when scaling raster images.
#[derive(ValueEnum, Clone, Copy, Debug, Default, Deserialize)]
#[serde(rename_all = "lowercase")]
pub enum Filter {
    Nearest,
    Triangle,
    CatmullRom,
    Gaussian,
    #[default]
    Lanczos3,
}

impl Filter {
    pub fn to_image(self) -> image::imageops::FilterType {
        use image::imageops::FilterType::*;
        match self {
            Filter::Nearest => Nearest,
            Filter::Triangle => Triangle,
            Filter::CatmullRom => CatmullRom,
            Filter::Gaussian => Gaussian,
            Filter::Lanczos3 => Lanczos3,
        }
    }
}

#[derive(Args, Debug)]
pub struct ResizeArgs {
    /// Input image path.
    pub input: PathBuf,
    /// Output path. Defaults next to input with a size suffix.
    #[arg(short, long)]
    pub output: Option<PathBuf>,
    /// Target width in pixels.
    #[arg(short = 'W', long)]
    pub width: Option<u32>,
    /// Target height in pixels.
    #[arg(short = 'H', long)]
    pub height: Option<u32>,
    /// Scale factor (e.g. 0.5). Mutually exclusive with width/height.
    #[arg(short, long)]
    pub scale: Option<f32>,
    /// Stretch to exact width AND height, ignoring aspect ratio.
    #[arg(long)]
    pub exact: bool,
    /// Resampling filter.
    #[arg(short, long, value_enum, default_value_t = Filter::default())]
    pub filter: Filter,
}

#[derive(Args, Debug)]
pub struct ConvertArgs {
    /// Input image path.
    pub input: PathBuf,
    /// Output path. Defaults next to input with the new extension.
    #[arg(short, long)]
    pub output: Option<PathBuf>,
    /// Target format.
    #[arg(short, long, value_enum)]
    pub to: OutFormat,
    /// JPEG/WebP quality (1-100) where applicable.
    #[arg(short, long, default_value_t = 90)]
    pub quality: u8,
}

#[derive(Args, Debug)]
pub struct RasterizeArgs {
    /// Input SVG path.
    pub input: PathBuf,
    /// Output PNG path. Defaults next to input.
    #[arg(short, long)]
    pub output: Option<PathBuf>,
    /// Target width in pixels (height derived from aspect ratio if omitted).
    #[arg(short = 'W', long)]
    pub width: Option<u32>,
    /// Target height in pixels.
    #[arg(short = 'H', long)]
    pub height: Option<u32>,
    /// Uniform scale relative to the SVG's intrinsic size.
    #[arg(short, long)]
    pub scale: Option<f32>,
}

#[derive(Args, Debug)]
pub struct SizesArgs {
    /// Input image or SVG path.
    pub input: PathBuf,
    /// Output directory.
    #[arg(short, long, default_value = "dist")]
    pub outdir: PathBuf,
    /// Comma-separated square sizes, e.g. 16,32,48,128.
    #[arg(
        short,
        long,
        value_delimiter = ',',
        default_value = "16,32,48,64,128,256"
    )]
    pub sizes: Vec<u32>,
    /// Output format for raster emission.
    #[arg(short = 't', long, value_enum, default_value_t = OutFormat::Png)]
    pub to: OutFormat,
    /// Resampling filter (raster inputs only).
    #[arg(short, long, value_enum, default_value_t = Filter::default())]
    pub filter: Filter,
}

#[derive(Args, Debug)]
pub struct InfoArgs {
    /// Input image path.
    pub input: PathBuf,
}

#[derive(Args, Debug)]
pub struct CurArgs {
    /// Input SVG or raster image.
    pub input: PathBuf,
    /// Output .cur path. Defaults next to input.
    #[arg(short, long)]
    pub output: Option<PathBuf>,
    /// Square size(s) to embed. Hotspot is given for the first size and scaled.
    #[arg(short, long, value_delimiter = ',', default_value = "32")]
    pub sizes: Vec<u32>,
    /// Hotspot X in pixels (at the first --sizes value).
    #[arg(long, default_value_t = 0)]
    pub hotspot_x: u32,
    /// Hotspot Y in pixels (at the first --sizes value).
    #[arg(long, default_value_t = 0)]
    pub hotspot_y: u32,
}

#[derive(Args, Debug)]
pub struct AniArgs {
    /// Input animated GIF.
    pub input: PathBuf,
    /// Output .ani path. Defaults next to input.
    #[arg(short, long)]
    pub output: Option<PathBuf>,
    /// Square frame size in pixels.
    #[arg(short, long, default_value_t = 32)]
    pub size: u32,
    /// Hotspot X in pixels.
    #[arg(long, default_value_t = 0)]
    pub hotspot_x: u32,
    /// Hotspot Y in pixels.
    #[arg(long, default_value_t = 0)]
    pub hotspot_y: u32,
    /// Force a constant frame rate (fps). Default: use the GIF's frame delays.
    #[arg(long)]
    pub fps: Option<u32>,
}

#[derive(Args, Debug)]
pub struct BatchArgs {
    /// Path to the catalog manifest (JSON).
    #[arg(short, long, default_value = "catalog/manifest.json")]
    pub manifest: PathBuf,
    /// Print the plan without writing files.
    #[arg(long)]
    pub dry_run: bool,
}
