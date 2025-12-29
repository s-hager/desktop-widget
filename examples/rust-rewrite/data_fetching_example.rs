// Example: Fetching stock data using yahoo-finance-api in Rust
// This demonstrates how to replace yfinance functionality

use yahoo_finance_api as yahoo;
use tokio;
use chrono::{Duration, Utc};
use anyhow::Result;

#[tokio::main]
async fn main() -> Result<()> {
    // Create a Yahoo Finance provider
    let provider = yahoo::YahooConnector::new();

    // Define the stock symbol
    let symbol = "AAPL";
    
    // Get current time and 1 month ago
    let end = Utc::now();
    let start = end - Duration::days(30);
    
    println!("Fetching {} data from {} to {}", symbol, start, end);

    // Fetch historical quotes
    let response = provider
        .get_quote_history(symbol, start, end)
        .await?;

    // Parse the response
    let quotes = response.quotes()?;
    
    println!("Fetched {} quotes", quotes.len());
    
    // Display some sample data
    if let Some(first_quote) = quotes.first() {
        println!("\nFirst quote:");
        println!("  Timestamp: {}", first_quote.timestamp);
        println!("  Open: ${:.2}", first_quote.open);
        println!("  High: ${:.2}", first_quote.high);
        println!("  Low: ${:.2}", first_quote.low);
        println!("  Close: ${:.2}", first_quote.close);
        println!("  Volume: {}", first_quote.volume);
    }

    if let Some(last_quote) = quotes.last() {
        println!("\nLast quote:");
        println!("  Timestamp: {}", last_quote.timestamp);
        println!("  Open: ${:.2}", last_quote.open);
        println!("  High: ${:.2}", last_quote.high);
        println!("  Low: ${:.2}", last_quote.low);
        println!("  Close: ${:.2}", last_quote.close);
        println!("  Volume: {}", last_quote.volume);
    }

    // Calculate percentage change
    if quotes.len() >= 2 {
        let first_close = quotes.first().unwrap().close;
        let last_close = quotes.last().unwrap().close;
        let percentage_change = ((last_close - first_close) / first_close) * 100.0;
        
        println!("\nPercentage change: {:.2}%", percentage_change);
    }

    // Get latest quote (real-time data)
    println!("\nFetching latest quote...");
    let latest = provider.get_latest_quotes(symbol, "1d").await?;
    let latest_quote = latest.last_quote()?;
    
    println!("Latest price: ${:.2}", latest_quote.close);
    
    Ok(())
}
