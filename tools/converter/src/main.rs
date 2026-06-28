//! kofun-convert — native asset converter for the kofun-friends library.
//!
//! Subcommands:
//!   resize     Resize a raster image (PNG/JPEG/WebP/GIF, animation-aware).
//!   convert    Convert between raster formats.
//!   rasterize  Render an SVG to PNG at a given size.
//!   sizes      Emit a raster/SVG at multiple sizes at once (icon/emoji/cursor sets).
//!   info       Print image metadata.
//!   batch      Process a directory tree driven by a catalog manifest.

mod cli;
mod cursor;
mod manifest;
mod raster;
mod svg;
mod util;

use clap::Parser;
use cli::{Cli, Command};

fn main() -> anyhow::Result<()> {
    let cli = Cli::parse();
    match cli.command {
        Command::Resize(a) => raster::resize(&a),
        Command::Convert(a) => raster::convert(&a),
        Command::Rasterize(a) => svg::rasterize(&a),
        Command::Sizes(a) => raster::sizes(&a),
        Command::Info(a) => raster::info(&a),
        Command::Cur(a) => cursor::cur(&a),
        Command::Ani(a) => cursor::ani(&a),
        Command::Batch(a) => manifest::run_batch(&a),
    }
}
