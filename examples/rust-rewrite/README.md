# Rust Rewrite Examples

This directory contains example code and configuration files to help with rewriting the desktop-widget application in Rust.

## Files

### 1. `Cargo.toml.example`
Example Cargo.toml file showing the recommended dependencies for a Rust rewrite. This includes:
- GUI frameworks (iced, egui, or Tauri)
- Plotting libraries (plotters, egui_plot)
- Financial data API (yahoo-finance-api)
- Data processing (polars, ndarray)
- Essential utilities (tokio, chrono, serde, etc.)

To use this file:
```bash
# Copy to your new Rust project
cp Cargo.toml.example /path/to/new-project/Cargo.toml

# Choose one GUI framework and comment out the others
# Then run:
cargo build
```

### 2. `data_fetching_example.rs`
Demonstrates how to fetch stock data using `yahoo-finance-api` as a replacement for the Python `yfinance` library.

Features shown:
- Fetching historical quotes for a given date range
- Getting the latest real-time quote
- Calculating percentage changes
- Async/await usage with tokio

To run this example:
```bash
# Add to your Cargo.toml dependencies section:
# yahoo-finance-api = "1.2"
# tokio = { version = "1", features = ["full"] }
# chrono = "0.4"
# anyhow = "1.0"

# Then compile and run:
cargo run --example data_fetching
```

### 3. `data_processing_example.rs`
Shows how to work with stock data using `polars` as a replacement for Python's `pandas` library.

Features shown:
- Creating DataFrames
- Accessing columns
- Calculating statistics (min, max, mean)
- Filtering data
- Adding calculated columns
- Selecting specific columns

To run this example:
```bash
# Add to your Cargo.toml dependencies section:
# polars = { version = "0.36", features = ["lazy"] }
# chrono = "0.4"
# anyhow = "1.0"

# Then compile and run:
cargo run --example data_processing
```

## Quick Start Guide

### Option 1: Starting from Scratch

1. Create a new Rust project:
```bash
cargo new desktop-widget-rust
cd desktop-widget-rust
```

2. Copy the example Cargo.toml:
```bash
cp examples/rust-rewrite/Cargo.toml.example Cargo.toml
```

3. Choose your GUI framework (uncomment one, comment out others in Cargo.toml)

4. Create the basic structure:
```bash
mkdir -p src/{ui,data,config}
```

5. Start implementing:
   - `src/data/` - Data fetching and processing (use data_fetching_example.rs as reference)
   - `src/ui/` - GUI code
   - `src/config/` - Configuration management
   - `src/main.rs` - Application entry point

### Option 2: Gradual Migration

1. Start by rewriting the data layer:
   - Implement stock data fetching
   - Port data processing logic
   - Create tests to verify correctness

2. Build a prototype UI:
   - Choose a GUI framework
   - Create basic window
   - Add stock chart rendering

3. Add features incrementally:
   - System tray icon
   - Settings management
   - Auto-refresh timer
   - Platform-specific features

## GUI Framework Comparison

### iced
**Best for**: Production desktop applications, modern UI/UX
```rust
// Example: Basic iced application structure
use iced::{Application, Settings};

struct StockWidget {
    // Application state
}

impl Application for StockWidget {
    // Implement required methods
}

fn main() -> iced::Result {
    StockWidget::run(Settings::default())
}
```

### egui
**Best for**: Developer tools, dashboards, rapid prototyping
```rust
// Example: Basic egui application structure
use eframe::egui;

fn main() {
    let options = eframe::NativeOptions::default();
    eframe::run_native(
        "Stock Widget",
        options,
        Box::new(|_cc| Box::new(MyApp::default())),
    );
}

struct MyApp;

impl eframe::App for MyApp {
    fn update(&mut self, ctx: &egui::Context, _frame: &mut eframe::Frame) {
        egui::CentralPanel::default().show(ctx, |ui| {
            ui.heading("Stock Chart");
            // Add chart and widgets here
        });
    }
}
```

### Tauri
**Best for**: Leveraging web technologies, cross-platform apps
```rust
// Rust backend (src-tauri/src/main.rs)
#[tauri::command]
async fn fetch_stock_data(symbol: String) -> Result<StockData, String> {
    // Fetch and return stock data
}

fn main() {
    tauri::Builder::default()
        .invoke_handler(tauri::generate_handler![fetch_stock_data])
        .run(tauri::generate_context!())
        .expect("error while running tauri application");
}
```
```javascript
// Frontend (JavaScript/TypeScript)
import { invoke } from '@tauri-apps/api/tauri';

async function loadStockData(symbol) {
    const data = await invoke('fetch_stock_data', { symbol });
    // Update UI with data
}
```

## Additional Resources

- See `RUST_REWRITE_RECOMMENDATIONS.md` in the root directory for detailed library comparisons
- [Rust Book](https://doc.rust-lang.org/book/) - Learn Rust fundamentals
- [Tokio Tutorial](https://tokio.rs/tokio/tutorial) - Async programming in Rust
- [Polars User Guide](https://pola-rs.github.io/polars-book/) - DataFrame operations

## Tips for Migration

1. **Start simple**: Don't try to port everything at once
2. **Use types**: Leverage Rust's type system for safety
3. **Handle errors**: Use `Result` and `?` operator properly
4. **Test incrementally**: Write tests as you go
5. **Profile performance**: Use `cargo flamegraph` to identify bottlenecks
6. **Keep Python version**: Run both during transition for comparison

## Common Gotchas

1. **Async/await**: Rust's async is different from Python's - you need a runtime (tokio)
2. **Lifetimes**: GUI frameworks may require understanding lifetimes
3. **String types**: Rust has multiple string types (`String`, `&str`) - this is by design
4. **Error handling**: No exceptions - use `Result<T, E>` instead
5. **Borrowing**: Understand ownership and borrowing rules early

## Performance Tips

1. Use `--release` mode for benchmarking: `cargo build --release`
2. Enable LTO (Link Time Optimization) in Cargo.toml
3. Consider using `polars` lazy API for data processing
4. Profile before optimizing: `cargo install flamegraph`
5. Use appropriate data structures (Vec, HashMap, etc.)

## Next Steps

1. Review the main recommendations document: `RUST_REWRITE_RECOMMENDATIONS.md`
2. Choose your technology stack based on your needs
3. Set up a new Rust project
4. Start with the data layer (easiest to port)
5. Build a minimal UI prototype
6. Iterate and add features

Good luck with your Rust rewrite! 🦀
