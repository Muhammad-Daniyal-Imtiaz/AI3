import gradio as gr
from playwright.async_api import async_playwright
from llama_index.tools.agentql import AgentQLBrowserToolSpec
import asyncio
import os

# Set your AgentQL API key (get it from https://www.agentql.com/)
os.environ["AGENTQL_API_KEY"] = "smWip19TVhUMKmZgZdFZVGXV2UtvlrKzQ_T3biyGIVvX2qAwqVdJyw"

async def scrape_olx():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        await page.goto("https://www.olx.in/items/q-iphone-15")
        
        # Use AgentQL to extract data
        agentql_tool = AgentQLBrowserToolSpec(async_browser=browser)
        results = await agentql_tool.extract_web_data_from_browser(
            """
            {
                listings[] {
                    title @ "h3"
                    price @ "span._89yzn"
                    location @ "span.tjgMj"
                    link @ "a" => href
                }
            }
            """
        )
        await browser.close()
        return results["listings"][:5]  # Return top 5 listings

async def scrape_amazon():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        await page.goto("https://www.amazon.in/s?k=iphone+15")
        
        # Use AgentQL to extract data
        agentql_tool = AgentQLBrowserToolSpec(async_browser=browser)
        results = await agentql_tool.extract_web_data_from_browser(
            """
            {
                products[] {
                    title @ "h2 a span"
                    price @ "span.a-price-whole"
                    rating @ "span.a-icon-alt"
                    link @ "h2 a" => href
                }
            }
            """
        )
        await browser.close()
        return results["products"][:5]  # Return top 5 products

async def get_iphone_data():
    olx_data = await scrape_olx()
    amazon_data = await scrape_amazon()
    
    output = "📱 iPhone 15 Listings\n\n"
    output += "=== OLX ===\n"
    for item in olx_data:
        output += f"📌 {item['title']}\n"
        output += f"💰 {item['price']}\n"
        output += f"📍 {item['location']}\n"
        output += f"🔗 {item['link']}\n\n"
    
    output += "\n=== Amazon ===\n"
    for item in amazon_data:
        output += f"📌 {item['title']}\n"
        output += f"💰 ₹{item['price']}\n"
        output += f"⭐ {item['rating']}\n"
        output += f"🔗 https://www.amazon.in{item['link']}\n\n"
    
    return output

def run_scraper():
    return asyncio.run(get_iphone_data())

# Gradio Interface
with gr.Blocks(title="iPhone 15 Price Scraper") as app:
    gr.Markdown("# 📱 iPhone 15 Price Comparison")
    gr.Markdown("Fetching latest prices from OLX and Amazon...")
    
    with gr.Row():
        scrape_btn = gr.Button("Scrape Latest Prices", variant="primary")
    
    output = gr.Textbox(label="Results", lines=20, interactive=False)
    
    scrape_btn.click(
        fn=run_scraper,
        outputs=output
    )

if __name__ == "__main__":
    app.launch()