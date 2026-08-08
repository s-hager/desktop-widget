# Rust Rewrite - Library Recommendations

This document provides recommendations for Rust libraries that would be suitable replacements for the key Python libraries used in the desktop-widget application.

## Overview

The desktop-widget application currently uses:
- **PyQt6** - GUI framework for creating the desktop widget window
- **PyQtGraph** - Fast plotting library for rendering stock charts
- **yfinance** - Library for fetching Yahoo Finance stock data
- **numpy/pandas** - Data manipulation and numerical operations
- **BlurWindow** - Background blur effects for Windows/macOS

## Key Library Replacements

### 1. GUI Framework (PyQt6 Replacement)

#### Option A: **iced** (Recommended)
- **Crate**: [`iced`](https://github.com/iced-rs/iced)
- **Description**: A cross-platform GUI library for Rust inspired by Elm
- **Pros**:
  - Native cross-platform support (Windows, macOS, Linux)
  - Modern, reactive architecture
  - GPU-accelerated rendering
  - Good performance
  - Active development and community
  - Built-in support for custom widgets
- **Cons**:
  - Younger ecosystem compared to Qt
  - Learning curve for the Elm architecture
- **Use case**: Best for building modern, responsive desktop applications

#### Option B: **egui**
- **Crate**: [`egui`](https://github.com/emilk/egui)
- **Description**: An immediate mode GUI library
- **Pros**:
  - Very easy to use and learn
  - Excellent for developer tools and dashboards
  - Fast iteration and development
  - Cross-platform
  - Good integration with various rendering backends
- **Cons**:
  - Immediate mode paradigm may not suit all use cases
  - Less suitable for traditional desktop applications
- **Use case**: Great for data visualization widgets and dashboards

#### Option C: **Slint**
- **Crate**: [`slint`](https://github.com/slint-ui/slint)
- **Description**: A declarative GUI toolkit for embedded and desktop
- **Pros**:
  - Declarative UI with `.slint` markup language
  - Native widgets option available
  - Good performance on embedded devices
  - Professional backing (SixtyFPS)
- **Cons**:
  - Smaller community
  - Some features require commercial license
- **Use case**: Good for applications needing both desktop and embedded support

#### Option D: **tauri** (with web frontend)
- **Crate**: [`tauri`](https://github.com/tauri-apps/tauri)
- **Description**: Framework for building desktop apps using web technologies
- **Pros**:
  - Use familiar web technologies (HTML/CSS/JS)
  - Small bundle size
  - Strong security model
  - Native system integration
  - Growing ecosystem
- **Cons**:
  - Not pure Rust (frontend is web-based)
  - Different paradigm from native GUI
- **Use case**: Best if you want to leverage web development skills

### 2. Charting/Plotting (PyQtGraph Replacement)

#### Option A: **plotters** (Recommended)
- **Crate**: [`plotters`](https://github.com/plotters-rs/plotters)
- **Description**: A Rust drawing library focused on data plotting
- **Pros**:
  - Pure Rust
  - Multiple backends (bitmap, SVG, Cairo, etc.)
  - Good performance
  - Extensive chart types
  - Can integrate with various GUI frameworks
  - Active development
- **Cons**:
  - May require manual integration with GUI framework
- **Use case**: Best for high-performance, customizable charts
- **Integration**: Works well with iced, egui, or standalone

#### Option B: **egui_plot**
- **Crate**: Part of [`egui`](https://github.com/emilk/egui)
- **Description**: Built-in plotting module for egui
- **Pros**:
  - Seamless integration with egui
  - Interactive plots out of the box
  - Easy to use
  - Real-time updates
- **Cons**:
  - Tied to egui framework
  - Less customization than plotters
- **Use case**: Best if using egui for GUI

#### Option C: **plotly** (Rust bindings)
- **Crate**: [`plotly`](https://github.com/igiagkiozis/plotly)
- **Description**: Rust bindings for Plotly.js
- **Pros**:
  - Rich, interactive visualizations
  - Web-based rendering
  - Professional-looking charts
- **Cons**:
  - Requires web view or HTML export
  - Heavier dependency
- **Use case**: Best for web-based or Tauri applications

### 3. Financial Data (yfinance Replacement)

#### Option A: **yahoo-finance-api** (Recommended)
- **Crate**: [`yahoo-finance-api`](https://github.com/xemwebe/yahoo_finance_api)
- **Description**: Rust library for accessing Yahoo Finance data
- **Pros**:
  - Direct replacement for yfinance
  - Async/await support
  - Type-safe API
  - Historical and real-time data
  - Active maintenance
- **Cons**:
  - Yahoo Finance API limitations apply
- **Use case**: Drop-in replacement for yfinance functionality

#### Option B: **yahoo_finance_rs**
- **Crate**: [`yahoo_finance_rs`](https://crates.io/crates/yahoo_finance_rs)
- **Description**: Another Yahoo Finance API wrapper
- **Pros**:
  - Simple API
  - Async support
- **Cons**:
  - Less active development
- **Use case**: Alternative if yahoo-finance-api doesn't meet needs

#### Option C: **Alpha Vantage API** (with reqwest)
- **Crate**: Use [`reqwest`](https://github.com/seanmonstar/reqwest) + custom implementation
- **Description**: Build custom client for Alpha Vantage or other API
- **Pros**:
  - More reliable data source (with API key)
  - Better rate limits with paid tier
  - Multiple data providers available
- **Cons**:
  - Requires API key
  - More work to implement
- **Use case**: For production apps needing reliable data

### 4. Data Manipulation (numpy/pandas Replacement)

#### **ndarray** + **polars**
- **Crates**: 
  - [`ndarray`](https://github.com/rust-ndarray/ndarray) - N-dimensional arrays (numpy replacement)
  - [`polars`](https://github.com/pola-rs/polars) - Fast DataFrame library (pandas replacement)
- **Description**: 
  - ndarray provides numpy-like arrays
  - polars provides pandas-like DataFrames with better performance
- **Pros**:
  - Excellent performance (polars is often faster than pandas)
  - Type-safe
  - Memory efficient
  - Good integration between libraries
- **Cons**:
  - Different API from pandas (less direct port)
- **Use case**: Essential for data processing in any Rust rewrite

### 5. Additional Recommended Libraries

#### **tokio** - Async Runtime
- **Crate**: [`tokio`](https://github.com/tokio-rs/tokio)
- **Description**: Asynchronous runtime for Rust
- **Why**: Essential for async operations like data fetching, timers
- **Use case**: Backend for async operations

#### **serde** + **serde_json** - Serialization
- **Crates**: 
  - [`serde`](https://github.com/serde-rs/serde)
  - [`serde_json`](https://github.com/serde-rs/json)
- **Description**: Serialization framework
- **Why**: For configuration files, API responses, data storage
- **Use case**: Configuration management

#### **chrono** - Date/Time
- **Crate**: [`chrono`](https://github.com/chronotope/chrono)
- **Description**: Date and time library
- **Why**: Essential for handling stock market timestamps
- **Use case**: All datetime operations

#### **anyhow** or **thiserror** - Error Handling
- **Crates**:
  - [`anyhow`](https://github.com/dtolnay/anyhow) - Easy error handling
  - [`thiserror`](https://github.com/dtolnay/thiserror) - Custom error types
- **Description**: Ergonomic error handling
- **Why**: Better error handling than Python exceptions
- **Use case**: Application-wide error handling

#### **config** or **confy** - Configuration
- **Crates**:
  - [`config`](https://github.com/mehcode/config-rs)
  - [`confy`](https://github.com/rust-cli/confy)
- **Description**: Configuration management libraries
- **Why**: Handle app settings, window positions, preferences
- **Use case**: Persistent application configuration

## Recommended Technology Stack

### Stack Option 1: Modern Native GUI (Recommended)
```toml
[dependencies]
# GUI Framework
iced = "0.12"
iced_native = "0.12"

# Plotting
plotters = "0.3"
plotters-iced = "0.1"  # Integration with iced

# Financial Data
yahoo-finance-api = "1.2"

# Data Processing
polars = { version = "0.36", features = ["lazy", "temporal"] }
ndarray = "0.15"

# Async Runtime
tokio = { version = "1", features = ["full"] }

# Utilities
chrono = "0.4"
serde = { version = "1.0", features = ["derive"] }
serde_json = "1.0"
anyhow = "1.0"
confy = "0.5"
```

**Pros**: Full native experience, best performance, most control
**Best for**: Desktop-first applications with complex interactions

### Stack Option 2: Immediate Mode GUI
```toml
[dependencies]
# GUI Framework
egui = "0.25"
eframe = { version = "0.25", features = ["default"] }

# Plotting (built-in)
# egui has egui_plot built-in

# Financial Data
yahoo-finance-api = "1.2"

# Data Processing
polars = { version = "0.36", features = ["lazy", "temporal"] }

# Async Runtime
tokio = { version = "1", features = ["full"] }

# Utilities
chrono = "0.4"
serde = { version = "1.0", features = ["derive"] }
anyhow = "1.0"
```

**Pros**: Simplest to develop, fast iteration, good for widgets
**Best for**: Dashboard-style applications, developer tools

### Stack Option 3: Web-Based Desktop App
```toml
[dependencies]
# Desktop Framework
tauri = { version = "1.5", features = ["shell-open"] }

# Backend API
axum = "0.7"  # Web framework for internal API

# Financial Data
yahoo-finance-api = "1.2"

# Data Processing
polars = { version = "0.36", features = ["lazy"] }

# Async Runtime
tokio = { version = "1", features = ["full"] }

# Utilities
chrono = "0.4"
serde = { version = "1.0", features = ["derive"] }
serde_json = "1.0"
anyhow = "1.0"
```

**Frontend**: React, Vue, or Svelte with Chart.js or Plotly
**Pros**: Leverage web skills, rapid UI development, modern look
**Best for**: Teams with web development experience

## Platform-Specific Considerations

### Windows
- For blur effects: [`windows-rs`](https://github.com/microsoft/windows-rs) for native Windows API calls
- System tray: Most GUI frameworks have system tray support
- Auto-start: Use Windows registry via `winreg` crate

### macOS
- For blur effects: Use Cocoa bindings via `objc` or `cocoa` crates
- Background app: Similar to Python implementation, use platform-specific APIs
- Auto-start: Use `LaunchAgents` plist files

### Linux
- System tray: Use freedesktop standards
- Blur effects: May require compositor-specific solutions
- Auto-start: Use `.desktop` files in autostart directory

## Migration Strategy Recommendations

1. **Start with data layer**: Implement financial data fetching with `yahoo-finance-api`
2. **Build core logic**: Port data processing using `polars` and `ndarray`
3. **Prototype UI**: Choose a GUI framework and create basic window
4. **Add charting**: Integrate plotting library with GUI framework
5. **Polish**: Add platform-specific features (blur, tray icon, auto-start)
6. **Optimize**: Profile and optimize performance bottlenecks

## Performance Expectations

Compared to Python implementation:
- **Startup time**: 5-10x faster
- **Memory usage**: 50-70% less
- **Chart rendering**: 2-5x faster
- **Data processing**: 10-50x faster (with polars)
- **Binary size**: Larger initially, but standalone (no Python runtime)

## Learning Resources

- **Rust Book**: https://doc.rust-lang.org/book/
- **iced tutorial**: https://book.iced.rs/
- **egui demo**: https://www.egui.rs/
- **Tauri guides**: https://tauri.app/v1/guides/
- **plotters examples**: https://github.com/plotters-rs/plotters#gallery
- **polars guide**: https://pola-rs.github.io/polars-book/

## Conclusion

For a desktop stock widget rewrite in Rust, I recommend:

1. **GUI**: **iced** or **egui** (depending on whether you prefer declarative vs immediate mode)
2. **Plotting**: **plotters** with iced, or **egui_plot** with egui
3. **Financial Data**: **yahoo-finance-api**
4. **Data Processing**: **polars** + **ndarray**

This combination provides the best balance of performance, developer experience, and community support while staying closest to the original functionality.
