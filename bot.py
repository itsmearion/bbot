import asyncio
import aiohttp
from pyrogram import Client
import matplotlib.pyplot as plt
import datetime
import io

API_ID = 22231144  # Ganti dengan API ID kamu
API_HASH = "772292211b49baaae83b06b714576cd3"
BOT_TOKEN = "7548554907:AAGrGHswMqnbYOEDUQPEDt1Df-bNqEb262E"
CHANNEL_ID = -1002658558109  # Ganti ke channel kamu

app = Client("toncoin_price_bot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)

last_price_usd = None

async def get_price():
    url = "https://api.coingecko.com/api/v3/simple/price?ids=toncoin&vs_currencies=usd,idr"
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as resp:
            data = await resp.json()
            return data["toncoin"]["usd"], data["toncoin"]["idr"]

async def get_price_history():
    url = "https://api.coingecko.com/api/v3/coins/toncoin/market_chart?vs_currency=usd&days=1&interval=hourly"
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as resp:
            data = await resp.json()
            return data["prices"]

def create_chart(prices):
    times = [datetime.datetime.fromtimestamp(p[0] / 1000) for p in prices]
    values = [p[1] for p in prices]

    plt.figure(figsize=(8, 4))
    plt.plot(times, values, color="blue", linewidth=2)
    plt.title("Harga Toncoin 24 Jam Terakhir (USD)")
    plt.xlabel("Waktu")
    plt.ylabel("Harga (USD)")
    plt.grid(True)
    plt.tight_layout()

    buf = io.BytesIO()
    plt.savefig(buf, format="png")
    buf.seek(0)
    plt.close()
    return buf

async def send_to_channel():
    global last_price_usd
    while True:
        try:
            price_usd, price_idr = await get_price()
            history = await get_price_history()
            chart = create_chart(history)

            message = f"""**Harga Toncoin (TON) Saat Ini**
💵 USD: `$ {price_usd:.4f}`
🇮🇩 IDR: `Rp {price_idr:,.0f}`"""

            if last_price_usd:
                change = (price_usd - last_price_usd) / last_price_usd * 100
                if abs(change) >= 3:
                    emoji = "📈" if change > 0 else "📉"
                    message += f"\n\n{emoji} Perubahan: `{change:+.2f}%` dibanding 1 menit lalu."

            await app.send_photo(CHANNEL_ID, photo=chart, caption=message)
            last_price_usd = price_usd

        except Exception as e:
            print("Gagal update harga:", e)

        await asyncio.sleep(60)

async def main():
    await app.start()
    await send_to_channel()

if __name__ == "__main__":
    asyncio.run(main())
