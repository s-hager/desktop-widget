// Example: Data processing with polars (pandas replacement)
// This demonstrates how to work with stock data similar to pandas

use polars::prelude::*;
use chrono::{DateTime, Utc};
use anyhow::Result;

fn main() -> Result<()> {
    // Example: Creating a DataFrame similar to pandas
    // Simulating stock data structure
    
    let dates = vec![
        "2024-01-01 09:00:00",
        "2024-01-01 10:00:00",
        "2024-01-01 11:00:00",
        "2024-01-01 12:00:00",
        "2024-01-01 13:00:00",
    ];
    
    let open_prices = vec![150.0, 151.5, 152.0, 151.0, 152.5];
    let high_prices = vec![152.0, 153.0, 153.5, 152.5, 154.0];
    let low_prices = vec![149.5, 151.0, 151.5, 150.5, 152.0];
    let close_prices = vec![151.5, 152.0, 151.0, 152.5, 153.0];
    let volumes = vec![1000000, 1200000, 950000, 1100000, 1300000];
    
    // Create a DataFrame
    let df = DataFrame::new(vec![
        Series::new("datetime", dates),
        Series::new("open", open_prices),
        Series::new("high", high_prices),
        Series::new("low", low_prices),
        Series::new("close", close_prices),
        Series::new("volume", volumes),
    ])?;
    
    println!("Stock Data DataFrame:");
    println!("{}", df);
    
    // Get column data (similar to df['Close'])
    let close_series = df.column("close")?;
    println!("\nClose prices:");
    println!("{}", close_series);
    
    // Calculate statistics
    println!("\nStatistics:");
    println!("Min close: {:.2}", close_series.min::<f64>().unwrap());
    println!("Max close: {:.2}", close_series.max::<f64>().unwrap());
    println!("Mean close: {:.2}", close_series.mean().unwrap());
    
    // Filter data (similar to df[df['volume'] > 1000000])
    let high_volume_df = df.clone().lazy()
        .filter(col("volume").gt(lit(1000000)))
        .collect()?;
    
    println!("\nHigh volume trades (> 1,000,000):");
    println!("{}", high_volume_df);
    
    // Calculate percentage change
    let close_values = close_series.f64()?;
    if let (Some(first), Some(last)) = (close_values.get(0), close_values.get(close_values.len() - 1)) {
        let pct_change = ((last - first) / first) * 100.0;
        println!("\nPercentage change: {:.2}%", pct_change);
    }
    
    // Add a new calculated column
    let df_with_range = df.lazy()
        .with_column(
            (col("high") - col("low")).alias("range")
        )
        .collect()?;
    
    println!("\nDataFrame with calculated range:");
    println!("{}", df_with_range);
    
    // Select specific columns (similar to df[['datetime', 'close']])
    let selected = df.select(["datetime", "close"])?;
    println!("\nSelected columns:");
    println!("{}", selected);
    
    Ok(())
}
