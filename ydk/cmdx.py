import asyncio
import json
import aiohttp
import websockets
import time

async def get_dms_and_messages():
    # Discord Gateway URL
    gateway_url = "wss://gateway.discord.gg/?v=9&encoding=json"
    
    # Token'ı config dosyasından oku
    with open('config.json') as f:
        config = json.load(f)
        token = config['token']

    async def maintain_connection():
        while True:
            try:
                async with websockets.connect(gateway_url) as websocket:
                    # İlk hello mesajını al
                    hello = await websocket.recv()
                    hello_data = json.loads(hello)
                    
                    # İlk identify paketi
                    await websocket.send(json.dumps({
                        "op": 2,
                        "d": {
                            "token": token,
                            "intents": 32767,
                            "properties": {
                                "$os": "windows",
                                "$browser": "chrome",
                                "$device": "pc"
                            },
                            "presence": {
                                "status": "online",
                                "afk": False
                            }
                        }
                    }))

                    # Heartbeat için
                    last_sequence = None
                    heartbeat_interval = hello_data['d']['heartbeat_interval']

                    async def heartbeat():
                        while True:
                            try:
                                await websocket.send(json.dumps({"op": 1, "d": last_sequence}))
                                await asyncio.sleep(heartbeat_interval / 1000)
                            except:
                                break

                    asyncio.create_task(heartbeat())

                    async def delete_message(session, channel_id, message_id):
                        url = f"https://discord.com/api/v9/channels/{channel_id}/messages/{message_id}"
                        max_retries = 5
                        retry_count = 0
                        
                        while retry_count < max_retries:
                            try:
                                async with session.delete(url, headers=headers) as resp:
                                    if resp.status == 204:
                                        return True
                                    elif resp.status == 429:  # Rate limit
                                        retry_after = float((await resp.json()).get('retry_after', 1))
                                        print(f"Rate limit aşıldı. {retry_after} saniye bekleniyor...")
                                        await asyncio.sleep(retry_after + 0.7)
                                        retry_count += 1
                                        continue
                                    else:
                                        print(f"Silme hatası: HTTP {resp.status}")
                                        return False
                            except Exception as e:
                                print(f"Silme hatası: {e}")
                                retry_count += 1
                                await asyncio.sleep(1)
                        return False

                    dm_channels = {}
                    selected_channel = None
                    user_id = None

                    # HTTP istemcisi oluştur
                    async with aiohttp.ClientSession() as session:
                        headers = {
                            "Authorization": token,
                            "Content-Type": "application/json"
                        }

                        # Önce kullanıcı bilgilerini al
                        async with session.get("https://discord.com/api/v9/users/@me", headers=headers) as resp:
                            if resp.status == 200:
                                user_data = await resp.json()
                                user_id = user_data["id"]

                        # DM kanallarını al
                        async with session.get("https://discord.com/api/v9/users/@me/channels", headers=headers) as resp:
                            if resp.status == 200:
                                channels = await resp.json()
                                print("\nDM Listesi:")
                                for i, channel in enumerate(channels, 1):
                                    if channel["type"] == 1:  # DM tipi
                                        recipients = channel["recipients"][0]
                                        dm_channels[i] = channel["id"]
                                        print(f"{i}- {recipients['username']}")

                                print("\n0- Tüm DM'lerdeki mesajlarımı sil")

                                while not selected_channel:
                                    try:
                                        choice = int(input("\nHangi kullanıcının mesajlarını görmek/silmek istersiniz? (Numara seçin): "))
                                        if choice == 0:
                                            print("\nTüm DM'lerdeki mesajlarınız siliniyor...")
                                            total_deleted = 0

                                            for channel_id in dm_channels.values():
                                                print(f"\nYeni DM kanalına geçiliyor...")
                                                last_message_id = None
                                                channel_deleted = 0
                                                
                                                while True:
                                                    url = f"https://discord.com/api/v9/channels/{channel_id}/messages?limit=100"
                                                    if last_message_id:
                                                        url += f"&before={last_message_id}"

                                                    try:
                                                        async with session.get(url, headers=headers) as resp:
                                                            if resp.status != 200:
                                                                print(f"Mesajları alma hatası: HTTP {resp.status}")
                                                                break

                                                            messages = await resp.json()
                                                            if not messages:
                                                                print("Bu DM'de başka mesaj bulunamadı.")
                                                                break

                                                            for msg in messages:
                                                                last_message_id = msg["id"]
                                                                if msg["author"]["id"] == user_id:
                                                                    if await delete_message(session, channel_id, msg["id"]):
                                                                        channel_deleted += 1
                                                                        total_deleted += 1
                                                                        print(f"Silinen mesaj ({channel_deleted}): {msg['content'][:50]}...")
                                                                        await asyncio.sleep(0.5)  # Rate limit için daha kısa bekleme
                                                    except Exception as e:
                                                        print(f"Beklenmeyen hata: {e}")
                                                        await asyncio.sleep(2)
                                                        continue

                                                print(f"Bu DM'de toplam {channel_deleted} mesaj silindi.")
                                                await asyncio.sleep(1)  # DM'ler arası bekleme

                                            print(f"\nToplam {total_deleted} mesaj silindi.")
                                            print("Programı kapatabilirsiniz.")
                                            return

                                        elif choice in dm_channels:
                                            selected_channel = dm_channels[choice]
                                            last_message_id = None
                                            deleted_count = 0

                                            while True:
                                                url = f"https://discord.com/api/v9/channels/{selected_channel}/messages?limit=100"
                                                if last_message_id:
                                                    url += f"&before={last_message_id}"

                                                async with session.get(url, headers=headers) as resp:
                                                    if resp.status != 200:
                                                        break

                                                    messages = await resp.json()
                                                    if not messages:
                                                        break

                                                    for msg in messages:
                                                        last_message_id = msg["id"]
                                                        if msg["author"]["id"] == user_id:
                                                            retry_count = 0
                                                            while retry_count < 3:  # Maximum 3 deneme
                                                                if await delete_message(session, selected_channel, msg["id"]):
                                                                    deleted_count += 1
                                                                    print(f"Silinen mesaj: {msg['content'][:100]}...")
                                                                    break
                                                                else:
                                                                    retry_count += 1
                                                                    print(f"Mesaj silme başarısız, yeniden deneniyor ({retry_count}/3)...")
                                                                    await asyncio.sleep(2)
                                                            
                                                            # Rate limit'e takılmamak için her mesaj silme işlemi arasında bekle
                                                            await asyncio.sleep(1.2)
                                                        else:
                                                            print(f"{msg['author']['username']}: {msg['content'][:100]}...")

                                            print(f"\nToplam {deleted_count} mesaj silindi.")
                                            print("Programı kapatabilirsiniz.")
                                            return
                                        else:
                                            print("Geçersiz seçim, lütfen tekrar deneyin.")
                                    except ValueError:
                                        print("Lütfen geçerli bir numara girin.")

                    while True:
                        try:
                            msg = await websocket.recv()
                            data = json.loads(msg)
                            if data.get('s'):
                                last_sequence = data['s']
                        except websockets.ConnectionClosed:
                            break
                        except Exception as e:
                            print(f"Mesaj işleme hatası: {e}")
                            continue

            except Exception as e:
                print(f"Bağlantı hatası: {e}")
                await asyncio.sleep(5)
                continue

    await maintain_connection()

async def main():
    await get_dms_and_messages()

if __name__ == "__main__":
    asyncio.run(main())
