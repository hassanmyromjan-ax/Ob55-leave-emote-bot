import requests , os , psutil , sys , jwt , pickle , json , binascii , time , urllib3 , base64 , datetime , re , socket , threading , ssl , pytz , aiohttp , asyncio
from flask import Flask, request, jsonify
from protobuf_decoder.protobuf_decoder import Parser
from xC4 import * ; from xHeaders import *
from datetime import datetime
from google.protobuf.timestamp_pb2 import Timestamp
from concurrent.futures import ThreadPoolExecutor
from threading import Thread
from Crypto.Cipher import AES
from Crypto.Util.Padding import pad
from Pb2 import DEcwHisPErMsG_pb2 , MajoRLoGinrEs_pb2 , PorTs_pb2 , MajoRLoGinrEq_pb2 , sQ_pb2 , Team_msg_pb2
from cfonts import render, say
import queue
import login_engine  # OB55 login flow
from types import SimpleNamespace
from flask import send_from_directory
from datetime import date


urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)  

# VariabLes dyli 
#------------------------------------------#
online_writer = None
whisper_writer = None
spam_room = False
spammer_uid = None
spam_chat_id = None
spam_uid = None
Spy = False
Chat_Leave = False
key = None
iv = None
region = None
BOT_UID = None
last_emote_time = 0
emote_cooldown = 0.08  # SPEED: 0.15 -> 0.08
# QUEUE SYSTEM
emote_queue = queue.Queue()
is_processing = False
queue_lock = threading.Lock()
#------------------------------------------#

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
STATIC_DIR = os.path.join(BASE_DIR, 'static')
app = Flask(__name__, static_folder=STATIC_DIR)

# === WEBSITE CONFIG (আগের website এর task system) ===
TASKS_CONFIG = [
    {"id": "task1", "name": "JOIN TELEGRAM CHANNEL", "link": "https://t.me/axemoteserver"},
    {"id": "task2", "name": "JOIN 2d TELEGRAM", "link": "https://t.me/axromjanyt"},
    {"id": "task3", "name": "SUBSCRIBE YOUTUBE", "link": "https://www.youtube.com/@axromjan"},
]
SETTINGS_CONFIG = {"maintenance": "off", "telegram": "https://t.me/axemoteserver"}

# === VISIT COUNTER (file-based) ===
VISITS_FILE = os.path.join(BASE_DIR, 'visits.json')
def load_visits():
    try:
        with open(VISITS_FILE, 'r') as f: return json.load(f)
    except Exception:
        return {"total": 0, "today": 0, "date": str(date.today())}
def save_visits(v):
    try:
        with open(VISITS_FILE, 'w') as f: json.dump(v, f)
    except Exception: pass
def record_visit():
    v = load_visits(); today = str(date.today())
    v["total"] = v.get("total", 0) + 1
    if v.get("date") != today: v["date"] = today; v["today"] = 1
    else: v["today"] = v.get("today", 0) + 1
    save_visits(v); return v

Hr = {
    'User-Agent': "Dalvik/2.1.0 (Linux; U; Android 11; ASUS_Z01QD Build/PI)",
    'Connection': "Keep-Alive",
    'Accept-Encoding': "gzip",
    'Content-Type': "application/x-www-form-urlencoded",
    'Expect': "100-continue",
    'X-Unity-Version': "2018.4.11f1",
    'X-GA': "v1 1",
    'ReleaseVersion': "OB55"}

# ---- Random Colores ----
def get_random_color():
    colors = [
        "[FF0000]", "[00FF00]", "[0000FF]", "[FFFF00]", "[FF00FF]", "[00FFFF]", "[FFFFFF]", "[FFA500]",
        "[A52A2A]", "[800080]", "[000000]", "[808080]", "[C0C0C0]", "[FFC0CB]", "[FFD700]", "[ADD8E6]",
        "[90EE90]", "[D2691E]", "[DC143C]", "[00CED1]", "[9400D3]", "[F08080]", "[20B2AA]", "[FF1493]",
        "[7CFC00]", "[B22222]", "[FF4500]", "[DAA520]", "[00BFFF]", "[00FF7F]", "[4682B4]", "[6495ED]",
        "[5F9EA0]", "[DDA0DD]", "[E6E6FA]", "[B0C4DE]", "[556B2F]", "[8FBC8F]", "[2E8B57]", "[3CB371]",
        "[6B8E23]", "[808000]", "[B8860B]", "[CD5C5C]", "[8B0000]", "[FF6347]", "[FF8C00]", "[BDB76B]",
        "[9932CC]", "[8A2BE2]", "[4B0082]", "[6A5ACD]", "[7B68EE]", "[4169E1]", "[1E90FF]", "[191970]",
        "[00008B]", "[000080]", "[008080]", "[008B8B]", "[B0E0E6]", "[AFEEEE]", "[E0FFFF]", "[F5F5DC]",
        "[FAEBD7]"
    ]
    return random.choice(colors)

# === OB55 LOGIN: login_engine.do_login() এর ভেতরে (GeNeRaTeAccEss / MajorLogin / GetLoginData) ===

async def DecodeWhisperMessage(hex_packet):
    packet = bytes.fromhex(hex_packet)
    proto = DEcwHisPErMsG_pb2.DecodeWhisper()
    proto.ParseFromString(packet)
    return proto

async def decode_team_packet(hex_packet):
    packet = bytes.fromhex(hex_packet)
    proto = sQ_pb2.recieved_chat()
    proto.ParseFromString(packet)
    return proto

# === OB55 AUTH PACKETS ===
async def xAuThSTarTuP(TarGeT, token, timestamp, key, iv):
    """Online server auth (OB55, opcode 830c) -> hex string"""
    return build_ob55_online_auth(int(TarGeT), token, int(timestamp), key, iv).hex()

async def xAuThChaT(TarGeT, token, timestamp, key, iv):
    """Chat server auth (OB55, opcode 6d19) -> hex string"""
    return create_auth_token_chat(int(TarGeT), token, int(timestamp), key, iv)

async def cHTypE(H):
    if not H: return 'Squid'
    elif H == 1: return 'CLan'
    elif H == 2: return 'PrivaTe'
    
async def SEndMsG(H , message , Uid , chat_id , key , iv):
    TypE = await cHTypE(H)
    if TypE == 'Squid': msg_packet = await xSEndMsgsQ(message , chat_id , key , iv)
    elif TypE == 'CLan': msg_packet = await xSEndMsg(message , 1 , chat_id , chat_id , key , iv)
    elif TypE == 'PrivaTe': msg_packet = await xSEndMsg(message , 2 , Uid , Uid , key , iv)
    return msg_packet

async def SEndPacKeT(OnLinE , ChaT , TypE , PacKeT):
    if TypE == 'ChaT' and ChaT: whisper_writer.write(PacKeT) ; await whisper_writer.drain()
    elif TypE == 'OnLine': online_writer.write(PacKeT) ; await online_writer.drain()
    else: return 'UnsoPorTed TypE ! >> ErrrroR (:():)' 
           
async def TcPOnLine(ip, port, key, iv, AutHToKen, reconnect_delay=0.5):
    global online_writer , spam_room , whisper_writer , spammer_uid , spam_chat_id , spam_uid , XX , uid , Spy,data2, Chat_Leave
    while True:
        try:
            reader , writer = await asyncio.open_connection(ip, int(port))
            online_writer = writer
            bytes_payload = bytes.fromhex(AutHToKen)
            online_writer.write(bytes_payload)
            await online_writer.drain()
            while True:
                data2 = await reader.read(9999)
                if not data2: break
                
                if data2.hex().startswith('0500'):
                    try:
                        print(data2.hex()[10:])
                        packet = await DeCode_PackEt(data2.hex()[10:])
                        print(packet)
                        packet = json.loads(packet)
                        OwNer_UiD , CHaT_CoDe , SQuAD_CoDe = await GeTSQDaTa(packet)

                        JoinCHaT = await AutH_Chat(3 , OwNer_UiD , CHaT_CoDe, key,iv)
                        await SEndPacKeT(whisper_writer , online_writer , 'ChaT' , JoinCHaT)


                        message = f'[B][C]{get_random_color()}\n- WeLComE To Emote Bot ! '
                        P = await SEndMsG(0 , message , OwNer_UiD , OwNer_UiD , key , iv)
                        await SEndPacKeT(whisper_writer , online_writer , 'ChaT' , P)

                    except:
                        if data2.hex().startswith('0500') and len(data2.hex()) > 1000:
                            try:
                                print(data2.hex()[10:])
                                packet = await DeCode_PackEt(data2.hex()[10:])
                                print(packet)
                                packet = json.loads(packet)
                                OwNer_UiD , CHaT_CoDe , SQuAD_CoDe = await GeTSQDaTa(packet)

                                JoinCHaT = await AutH_Chat(3 , OwNer_UiD , CHaT_CoDe, key,iv)
                                await SEndPacKeT(whisper_writer , online_writer , 'ChaT' , JoinCHaT)


                                message = f'[B][C]{get_random_color()}\n- WeLComE To Emote Bot ! \n\n{get_random_color()}- Commands : @a {xMsGFixinG("123456789")} {xMsGFixinG("909000001")}\n\n[00FF00]Dev : @{xMsGFixinG("DEVXTLIVE")}'
                                P = await SEndMsG(0 , message , OwNer_UiD , OwNer_UiD , key , iv)
                                await SEndPacKeT(whisper_writer , online_writer , 'ChaT' , P)
                            except:
                                pass

            online_writer.close() ; await online_writer.wait_closed() ; online_writer = None

        except Exception as e: print(f"- ErroR With {ip}:{port} - {e}") ; online_writer = None
        await asyncio.sleep(reconnect_delay)
                            
async def TcPChaT(ip, port, AutHToKen, key, iv, LoGinDaTaUncRypTinG, ready_event, region , reconnect_delay=0.5):
    print(region, 'TCP CHAT')

    global spam_room , whisper_writer , spammer_uid , spam_chat_id , spam_uid , online_writer , chat_id , XX , uid , Spy,data2, Chat_Leave
    while True:
        try:
            reader , writer = await asyncio.open_connection(ip, int(port))
            whisper_writer = writer
            bytes_payload = bytes.fromhex(AutHToKen)
            whisper_writer.write(bytes_payload)
            await whisper_writer.drain()
            ready_event.set()
            if LoGinDaTaUncRypTinG.Clan_ID:
                clan_id = LoGinDaTaUncRypTinG.Clan_ID
                clan_compiled_data = LoGinDaTaUncRypTinG.Clan_Compiled_Data
                print('\n - TarGeT BoT in CLan ! ')
                print(f' - Clan Uid > {clan_id}')
                print(f' - BoT ConnEcTed WiTh CLan ChaT SuccEssFuLy ! ')
                pK = await AuthClan(clan_id , clan_compiled_data , key , iv)
                if whisper_writer: whisper_writer.write(pK) ; await whisper_writer.drain()
            while True:
                data = await reader.read(9999)
                if not data: break
                
                if data.hex().startswith("120000"):

                    msg = await DeCode_PackEt(data.hex()[10:])
                    chatdata = json.loads(msg)
                    try:
                        response = await DecodeWhisperMessage(data.hex()[10:])
                        uid = response.Data.uid
                        chat_id = response.Data.Chat_ID
                        XX = response.Data.chat_type
                        inPuTMsG = response.Data.msg.lower()
                    except:
                        response = None


                    if response:
                        if inPuTMsG.startswith(("/5")):
                            try:
                                dd = chatdata['5']['data']['16']
                                print('msg in private')
                                message = f"[B][C]{get_random_color()}\n\nAccepT My InV FasT\n\n"
                                P = await SEndMsG(response.Data.chat_type , message , uid , chat_id , key , iv)
                                await SEndPacKeT(whisper_writer , online_writer , 'ChaT' , P)
                                PAc = await OpEnSq(key , iv,region)
                                await SEndPacKeT(whisper_writer , online_writer , 'OnLine' , PAc)
                                C = await cHSq(5, uid ,key, iv,region)
                                await asyncio.sleep(0.05)  # SPEED: 0.1 -> 0.05
                                await SEndPacKeT(whisper_writer , online_writer , 'OnLine' , C)
                                V = await SEnd_InV(5 , uid , key , iv,region)
                                await asyncio.sleep(0.05)  # SPEED: 0.1 -> 0.05
                                await SEndPacKeT(whisper_writer , online_writer , 'OnLine' , V)
                                E = await ExiT(None , key , iv)
                                await asyncio.sleep(0.3)   # SPEED: 0.8 -> 0.3 (FAST LEAVE)
                                await SEndPacKeT(whisper_writer , online_writer , 'OnLine' , E)
                            except:
                                print('msg in squad')



                        if inPuTMsG.startswith('/x/'):
                            CodE = inPuTMsG.split('/x/')[1]
                            try:
                                dd = chatdata['5']['data']['16']
                                print('msg in private')
                                EM = await GenJoinSquadsPacket(CodE , key , iv)
                                await SEndPacKeT(whisper_writer , online_writer , 'OnLine' , EM)


                            except:
                                print('msg in squad')

                        if inPuTMsG.startswith('leave'):
                            leave = await ExiT(uid,key,iv)
                            await SEndPacKeT(whisper_writer , online_writer , 'OnLine' , leave)

                        if inPuTMsG.strip().startswith('/s'):
                            EM = await FS(key , iv)
                            await SEndPacKeT(whisper_writer , online_writer , 'OnLine' , EM)


                        if inPuTMsG.strip().startswith('/f'):

                            try:
                                dd = chatdata['5']['data']['16']
                                print('msg in private')
                                message = f"[B][C]{get_random_color()}\n\nOnLy In SQuaD ! \n\n"
                                P = await SEndMsG(response.Data.chat_type, message, uid, chat_id, key, iv)
                                await SEndPacKeT(whisper_writer, online_writer, 'ChaT', P)

                            except:
                                print('msg in squad')

                                parts = inPuTMsG.strip().split()
                                print(response.Data.chat_type, uid, chat_id)
                                message = f'[B][C]{get_random_color()}\nACITVE TarGeT -> {xMsGFixinG(uid)}\n'

                                P = await SEndMsG(response.Data.chat_type, message, uid, chat_id, key, iv)

                                uid2 = uid3 = uid4 = uid5 = uid6 = None
                                s = False

                                try:
                                    uid = int(parts[1])
                                    uid2 = int(parts[2])
                                    uid3 = int(parts[3])
                                    uid4 = int(parts[4])
                                    uid5 = int(parts[5])
                                    uid6 = int(parts[6])
                                    idT = int(parts[6])

                                except ValueError as ve:
                                    print("ValueError:", ve)
                                    s = True

                                except Exception:
                                    idT = len(parts) - 1
                                    idT = int(parts[idT])
                                    print(idT)
                                    print(uid)

                                if not s:
                                    try:
                                        await SEndPacKeT(whisper_writer, online_writer, 'ChaT', P)

                                        for i in range(50):
                                            print(f"Fast Emote {i+1}")
                                            H = await Emote_k(uid, idT, key, iv, region)
                                            await SEndPacKeT(whisper_writer, online_writer, 'OnLine', H)

                                            if uid2:
                                                H = await Emote_k(uid2, idT, key, iv, region)
                                                await SEndPacKeT(whisper_writer, online_writer, 'OnLine', H)
                                            if uid3:
                                                H = await Emote_k(uid3, idT, key, iv, region)
                                                await SEndPacKeT(whisper_writer, online_writer, 'OnLine', H)
                                            if uid4:
                                                H = await Emote_k(uid4, idT, key, iv, region)
                                                await SEndPacKeT(whisper_writer, online_writer, 'OnLine', H)
                                            if uid5:
                                                H = await Emote_k(uid5, idT, key, iv, region)
                                                await SEndPacKeT(whisper_writer, online_writer, 'OnLine', H)
                                            if uid6:
                                                H = await Emote_k(uid6, idT, key, iv, region)
                                                await SEndPacKeT(whisper_writer, online_writer, 'OnLine', H)

                                            await asyncio.sleep(0.06)  # SPEED: 0.12 -> 0.06

                                    except Exception as e:
                                        print("Fast emote error:", e)

                        if inPuTMsG.strip().startswith('/d'):

                            try:
                                dd = chatdata['5']['data']['16']
                                print('msg in private')
                                message = f"[B][C]{get_random_color()}\n\nOnLy In SQuaD ! \n\n"
                                P = await SEndMsG(response.Data.chat_type, message, uid, chat_id, key, iv)
                                await SEndPacKeT(whisper_writer, online_writer, 'ChaT', P)

                            except:
                                print('msg in squad')

                                parts = inPuTMsG.strip().split()
                                print(response.Data.chat_type, uid, chat_id)
                                message = f'[B][C]{get_random_color()}\nACITVE TarGeT -> {xMsGFixinG(uid)}\n'

                                P = await SEndMsG(response.Data.chat_type, message, uid, chat_id, key, iv)

                                uid2 = uid3 = uid4 = uid5 = uid6 = None
                                s = False

                                try:
                                    uid = int(parts[1])
                                    uid2 = int(parts[2])
                                    uid3 = int(parts[3])
                                    uid4 = int(parts[4])
                                    uid5 = int(parts[5])
                                    uid6 = int(parts[6])
                                    idT = int(parts[6])

                                except ValueError as ve:
                                    print("ValueError:", ve)
                                    s = True

                                except Exception:
                                    idT = len(parts) - 1
                                    idT = int(parts[idT])
                                    print(idT)
                                    print(uid)

                                if not s:
                                    try:
                                        await SEndPacKeT(whisper_writer, online_writer, 'ChaT', P)

                                        H = await Emote_k(uid, idT, key, iv,region)
                                        await SEndPacKeT(whisper_writer, online_writer, 'OnLine', H)

                                        if uid2:
                                            H = await Emote_k(uid2, idT, key, iv,region)
                                            await SEndPacKeT(whisper_writer, online_writer, 'OnLine', H)
                                        if uid3:
                                            H = await Emote_k(uid3, idT, key, iv,region)
                                            await SEndPacKeT(whisper_writer, online_writer, 'OnLine', H)
                                        if uid4:
                                            H = await Emote_k(uid4, idT, key, iv,region)
                                            await SEndPacKeT(whisper_writer, online_writer, 'OnLine', H)
                                        if uid5:
                                            H = await Emote_k(uid5, idT, key, iv,region)
                                            await SEndPacKeT(whisper_writer, online_writer, 'OnLine', H)
                                            if uid6:
                                                H = await Emote_k(uid6, idT, key, iv, region)
                                                await SEndPacKeT(whisper_writer, online_writer, 'OnLine', H)
                                        
                                        await asyncio.sleep(0.05)  # SPEED: 0.1 -> 0.05

                                    except Exception as e:
                                        pass


                        if inPuTMsG in ("dev"):
                            uid = response.Data.uid
                            chat_id = response.Data.Chat_ID
                            message = '/d <uid1> <uid2>... <emoteid> /f <uid1> <uid2>... <emoteid> for fast emote'
                            P = await SEndMsG(response.Data.chat_type , message , uid , chat_id , key , iv)
                            await SEndPacKeT(whisper_writer , online_writer , 'ChaT' , P)
                        response = None
                            
            whisper_writer.close() ; await whisper_writer.wait_closed() ; whisper_writer = None
                    
                    	
                    	
        except Exception as e: print(f"ErroR {ip}:{port} - {e}") ; whisper_writer = None
        await asyncio.sleep(reconnect_delay)
# ---------------------- FLASK ROUTES ----------------------

loop = None

async def perform_emote(team_code: str, uids: list, emote_id: int, request_id: int):
    global key, iv, region, online_writer, BOT_UID, whisper_writer, last_emote_time

    print(f"[Request {request_id}] Starting emote for team {team_code}")

    if online_writer is None:
        raise Exception("Bot not connected - online_writer is None")

    # Rate limiting check
    current_time = time.time()
    time_since_last = current_time - last_emote_time
    if time_since_last < emote_cooldown:
        wait_time = emote_cooldown - time_since_last
        print(f"[Request {request_id}] Waiting {wait_time:.2f}s for cooldown...")
        await asyncio.sleep(wait_time)
    
    last_emote_time = time.time()

    try:
        # 1. JOIN SQUAD
        print(f"[Request {request_id}] Joining squad...")
        EM = await GenJoinSquadsPacket(team_code, key, iv)
        await SEndPacKeT(None, online_writer, 'OnLine', EM)
        await asyncio.sleep(0.15)  # SPEED: 0.3 -> 0.15 (FAST JOIN)

        # 2. PERFORM EMOTE
        print(f"[Request {request_id}] Sending emotes...")
        for i, uid_str in enumerate(uids):
            uid = int(uid_str)
            H = await Emote_k(uid, emote_id, key, iv, region)
            await SEndPacKeT(None, online_writer, 'OnLine', H)
            print(f"[Request {request_id}] Emote {i+1}/{len(uids)} sent to {uid}")
            
            if i < len(uids) - 1:
                await asyncio.sleep(0.04)  # SPEED: 0.08 -> 0.04

        # 3. WAIT BEFORE LEAVE
        print(f"[Request {request_id}] Waiting before leave...")
        await asyncio.sleep(0.2)  # SPEED: 0.5 -> 0.2
        
        # 4. LEAVE SQUAD
        if BOT_UID:
            print(f"[Request {request_id}] Leaving squad...")
            LV = await ExiT(BOT_UID, key, iv)
            await SEndPacKeT(None, online_writer, 'OnLine', LV)
            print(f"[Request {request_id}] Left squad successfully")
        
        # SPEED: Fast cleanup
        await asyncio.sleep(0.2)  # SPEED: 0.5 -> 0.2
        
        last_emote_time = time.time()
        
        print(f"[Request {request_id}] COMPLETED successfully")
        return {"status": "success", "message": f"Emote done & bot left (Request {request_id})"}

    except Exception as e:
        print(f"[Request {request_id}] ERROR: {e}")
        raise Exception(f"Failed to perform emote: {str(e)}")


def process_queue():
    """Background thread to process queue items one by one"""
    global is_processing, loop
    
    while True:
        try:
            # Get item from queue with timeout
            item = emote_queue.get(timeout=1)
            team_code, uids, emote_id, request_id = item
            
            print(f"[Queue] Processing request {request_id}, queue size: {emote_queue.qsize()}")
            
            # Process in asyncio loop
            future = asyncio.run_coroutine_threadsafe(
                perform_emote(team_code, uids, emote_id, request_id), 
                loop
            )
            
            # Wait for completion with timeout
            try:
                result = future.result(timeout=30)
                print(f"[Queue] Request {request_id} completed: {result}")
            except Exception as e:
                print(f"[Queue] Request {request_id} failed: {e}")
            
            # SPEED: Faster queue processing
            time.sleep(0.5)  # SPEED: 1.0 -> 0.5
            
            emote_queue.task_done()
            
        except queue.Empty:
            continue
        except Exception as e:
            print(f"[Queue] Error: {e}")
            time.sleep(0.5)


@app.route('/join')
def join_team():
    global loop, is_processing
    team_code = request.args.get('tc')
    uid1 = request.args.get('uid1')
    uid2 = request.args.get('uid2')
    uid3 = request.args.get('uid3')
    uid4 = request.args.get('uid4')
    uid5 = request.args.get('uid5')
    uid6 = request.args.get('uid6')
    emote_id_str = request.args.get('emote_id')

    request_id = int(time.time() * 1000) % 10000
    
    print(f"[API] New request {request_id} - Team: {team_code}, UIDs: {uid1}, Emote: {emote_id_str}")

    if not team_code or not emote_id_str:
        return jsonify({"status": "error", "message": "Missing tc or emote_id"})

    try:
        emote_id = int(emote_id_str)
    except:
        return jsonify({"status": "error", "message": "emote_id must be integer"})

    uids = [uid for uid in [uid1, uid2, uid3, uid4, uid5, uid6] if uid]

    if not uids:
        return jsonify({"status": "error", "message": "Provide at least one UID"})

    # Add to queue
    queue_position = emote_queue.qsize() + 1
    emote_queue.put((team_code, uids, emote_id, request_id))
    
    print(f"[API] Request {request_id} added to queue at position {queue_position}")

    return jsonify({
        "status": "queued",
        "request_id": request_id,
        "team_code": team_code,
        "uids": uids,
        "emote_id": emote_id_str,
        "queue_position": queue_position,
        "message": f"Added to queue at position {queue_position}. Bot will process soon."
    })


# ---------------------- WEBSITE ROUTES ----------------------
@app.route('/')
def index():
    record_visit()
    return send_from_directory(STATIC_DIR, 'index.html')

@app.route('/style.css')
def css():
    return send_from_directory(STATIC_DIR, 'style.css')

@app.route('/script.js')
def js():
    return send_from_directory(STATIC_DIR, 'script.js')

@app.route('/api/tasks')
def get_tasks():
    return jsonify(TASKS_CONFIG)

@app.route('/api/settings')
def get_settings():
    return jsonify(SETTINGS_CONFIG)

@app.route('/api/servers')
def get_servers():
    return jsonify([{"name": "AX SERVER BD", "url": "/join"}])

@app.route('/api/visits')
def get_visits():
    v = load_visits()
    return jsonify({"total": v.get("total", 0), "today": v.get("today", 0)})

@app.route('/api/status')
def bot_status():
    return jsonify({"status": "online" if online_writer is not None else "offline",
                    "uid": str(BOT_UID) if BOT_UID else None})


def run_flask():
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port, debug=False, use_reloader=False)


# ---------------------- MAIN BOT SYSTEM ----------------------

async def MaiiiinE():
    global loop, key, iv, region, BOT_UID

    # BOT LOGIN UID
    BOT_UID = int('14539159640')

    Uid, Pw = '4396655574', 'JANVAI_AV0EW_BY_SPIDEERIO_GAMING_EAN8L'

    result = await login_engine.do_login(Uid, Pw, "BD")
    if not result:
        print("ErroR - Login Failed (InvaLid AccounT / BannEd / Server)")
        return None

    UrL = result["server_url"]
    print(UrL)
    region = result["region"]
    ToKen = result["token"]
    TarGeT = result["bot_uid"]
    key = result["key"]
    iv = result["iv"]
    timestamp = result["timestamp"]
    BOT_UID = int(TarGeT)   # OB55: লগইন করা account এর আসল UID

    loop = asyncio.get_running_loop()

    OnLineiP, OnLineporT = result["online_ip"], result["online_port"]
    ChaTiP, ChaTporT = result["chat_ip"], result["chat_port"]
    acc_name = result["account_name"]
    LoGinDaTaUncRypTinG = SimpleNamespace(
        Clan_ID=result.get("clan_id") or 0,
        Clan_Compiled_Data=result.get("clan_data") or "",
    )
    print(ToKen)

    await equie_emote(ToKen, UrL)

    AutHToKen = await xAuThSTarTuP(int(TarGeT), ToKen, int(timestamp), key, iv)   # online 830c
    ChaTAutH = await xAuThChaT(int(TarGeT), ToKen, int(timestamp), key, iv)       # chat 6d19
    ready_event = asyncio.Event()

    task1 = asyncio.create_task(
        TcPChaT(ChaTiP, ChaTporT, ChaTAutH, key, iv,
                LoGinDaTaUncRypTinG, ready_event, region)
    )

    await ready_event.wait()
    await asyncio.sleep(1)

    task2 = asyncio.create_task(
        TcPOnLine(OnLineiP, OnLineporT, key, iv, AutHToKen)
    )

    os.system('clear')
    print(render('DEV', colors=['white', 'green'], align='center'))
    print(f"\n - BoT STarTinG And OnLine on TarGet : {TarGeT} | BOT NAME : {acc_name}")
    print(" - BoT sTaTus > GooD | OnLinE ! (: \n")
    print(" - Queue System Active - Processing requests one by one\n")

    # Start queue processor thread
    queue_thread = threading.Thread(target=process_queue, daemon=True)
    queue_thread.start()

    flask_thread = threading.Thread(target=run_flask, daemon=True)
    flask_thread.start()

    await asyncio.gather(task1, task2)


async def StarTinG():
    while True:
        try:
            await asyncio.wait_for(MaiiiinE(), timeout=7 * 60 * 60)
        except asyncio.TimeoutError:
            print("Token ExpiRed ! , ResTartinG")
        except Exception as e:
            print(f"ErroR TcP - {e} => ResTarTinG ...")


if __name__ == '__main__':
    asyncio.run(StarTinG())
