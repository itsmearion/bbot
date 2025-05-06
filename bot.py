import asyncio
import logging
from aiogram import Bot, Dispatcher
from aiogram.types import InputFile
from apscheduler.schedulers.asyncio import AsyncIOScheduler
import aiohttp
import matplotlib.pyplot as plt
from datetime import datetime, timedelta
import os

# ENVIRONMENT VARIABLES
BOT_TOKEN = os.getenv("BOT_TOKEN")
CHANNEL_ID = os.getenv("CHANNEL_ID")  # Format: '@channelusername'

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()
scheduler = AsyncIOScheduler()

COINGECKO_API = "https://api.coingecko.com/api/v3"


async def fetch_prices():
    async with aiohttp.ClientSession() as session:
        async with session.get(f"{COINGECKO_API}/simple/price?ids=toncoin&vs_currencies=usd,idr") as resp:
            data = await resp.json()
        async with session.get(f"{COINGECKO_API}/coins/toncoin") as resp:
            meta = await resp.json()
    return {
        "price_idr": data['toncoin']['idr'],
        "price_usd": data['toncoin']['usd'],
        "market_cap": meta['market_data']['market_cap']['usd'],
        "cg_url": meta['links']['homepage'][0],
        "cmc_url": "https://coinmarketcap.com/currencies/toncoin/"
    }


async def fetch_weekly_chart():
    today = datetime.utcnow()
    from_ts = int((today - timedelta(days=7)).timestamp())
    to_ts = int(today.timestamp())

    async with aiohttp.ClientSession() as session:
        async with session.get(f"{COINGECKO_API}/coins/toncoin/market_chart/range?vs_currency=usd&from={from_ts}&to={to_ts}") as resp:
            data = await resp.json()

    prices = data['prices']  # [ [timestamp, price], ... ]
    times = [datetime.fromtimestamp(p[0] / 1000) for p in prices]
    values = [p[1] for p in prices]

    plt.figure(figsize=(10, 5))
    plt.plot(times, values, label='TON Price (USD)')
    plt.title("TON Coin - Weekly Price")
    plt.xlabel("Date")
    plt.ylabel("Price (USD)")
    plt.grid(True)
    plt.legend()
    chart_path = "/tmp/toncoin_chart.png"
    plt.savefig(chart_path)
    plt.close()
    return chart_path


async def send_update():
    try:
        data = await fetch_prices()
        chart_path = await fetch_weekly_chart()

        message = (
            f"💸 <b>Harga TON</b>\n"
            f"USD: <code>${data['price_usd']:,.2f}</code>\n"
            f"IDR: <code>Rp{data['price_idr']:,.0f}</code>\n\n"
            f"🪙 <b>Market Cap</b>: <code>${data['market_cap']:,.0f}</code>\n\n"
            f"♎️ <a href=\"{data['cg_url']}\">CoinGecko</a> | <a href=\"{data['cmc_url']}\">CoinMarketCap</a>"
        )

        await bot.send_photo(
            chat_id=CHANNEL_ID,
            photo=InputFile(chart_path),
            caption=message,
            parse_mode="HTML"
        )
    except Exception as e:
        logging.error(f"Gagal kirim update: {e}")


async def main():
    scheduler.add_job(send_update, "interval", minutes=10)
    scheduler.start()
    await dp.start_polling(bot)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    asyncio.run(main())
