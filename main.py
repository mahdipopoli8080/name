import asyncio
import sqlite3
import time
import random
import aiohttp
from telethon import TelegramClient, events, Button
from telethon.sessions import MemorySession
from telethon.errors import MessageNotModifiedError

# ==================== CONFIG ====================
API_ID = 8477522
API_HASH = '366c19cf69e02cad530261ad81212a85'
BOT_TOKEN = '8188613530:AAHnyK3MG-7mHe7tzlnnyOV-WT5WKGzsgeg'
ADMIN_ID = 5190717598
SMSBOWER_API_KEY = 'd7FVPDHaenCSNq05X1lzSlpQ6Ud30kff'
SMSBOWER_URL = 'https://smsbower.page/stubs/handler_api.php'
# ================================================

# ==================== FAKE NAMES API ====================
async def get_fake_name():
    """Get a random fake name from multiple sources"""
    sources = [
        'https://api.namefake.com/',
        'https://randomuser.me/api/',
    ]
    # Try randomuser.me
    try:
        async with aiohttp.ClientSession() as s:
            async with s.get('https://randomuser.me/api/?nat=us,gb,ru,de', timeout=aiohttp.ClientTimeout(total=5)) as r:
                data = await r.json()
                if 'results' in data and data['results']:
                    u = data['results'][0]
                    first = u['name']['first'].title()
                    last = u['name']['last'].title()
                    return f"{first} {last}"
    except: pass
    # Fallback: random from large list
    first_names = [
        'James','Mary','Robert','Patricia','John','Jennifer','Michael','Linda','David','Elizabeth',
        'William','Barbara','Richard','Susan','Joseph','Jessica','Thomas','Sarah','Christopher','Karen',
        'Charles','Lisa','Daniel','Nancy','Matthew','Betty','Anthony','Margaret','Mark','Sandra',
        'Donald','Ashley','Steven','Kimberly','Paul','Emily','Andrew','Donna','Joshua','Michelle',
        'Kenneth','Carol','Kevin','Amanda','Brian','Dorothy','George','Melissa','Timothy','Deborah',
        'Ronald','Stephanie','Edward','Rebecca','Jason','Sharon','Jeffrey','Laura','Ryan','Cynthia',
        'Jacob','Kathleen','Gary','Amy','Nicholas','Angela','Eric','Shirley','Jonathan','Anna',
        'Stephen','Brenda','Larry','Pamela','Justin','Emma','Scott','Nicole','Brandon','Helen',
        'Benjamin','Samantha','Samuel','Katherine','Raymond','Christine','Gregory','Debra','Frank','Rachel',
        'Alexander','Carolyn','Patrick','Janet','Jack','Catherine','Dennis','Maria','Jerry','Heather',
        'Tyler','Diane','Aaron','Ruth','Jose','Julie','Adam','Olivia','Nathan','Joyce',
        'Henry','Virginia','Douglas','Victoria','Zachary','Kelly','Peter','Lauren','Kyle','Christina',
        'Noah','Joan','Ethan','Evelyn','Jeremy','Judith','Walter','Megan','Christian','Andrea',
        'Keith','Cheryl','Roger','Hannah','Terry','Jacqueline','Austin','Martha','Sean','Gloria',
        'Gerald','Teresa','Carl','Ann','Harold','Sara','Dylan','Madison','Arthur','Frances',
        'Lawrence','Kathryn','Jordan','Janice','Jesse','Jean','Bryan','Abigail','Billy','Alice',
        'Bruce','Judy','Gabriel','Sophia','Joe','Grace','Logan','Denise','Albert','Amber',
        'Willie','Doris','Alan','Marilyn','Eugene','Danielle','Russell','Beverly','Vincent','Isabella',
        'Philip','Theresa','Bobby','Diana','Johnny','Natalie','Bradley','Brittany','Roy','Charlotte',
        'Elijah','Marie','Randy','Kayla','Wayne','Alexis','Howard','Lori','Ethan','Linda',
        'Vincent','Rosa','Craig','Alyssa','Philip','James','Bobby','Anna','Johnny','Samantha',
        'Ralph','Katherine','Roy','Christine','Eugene','Debra','Randy','Rachel','Louis','Carolyn',
        'Philip','Janet','Billy','Catherine','Austin','Maria','Harry','Heather','Bobby','Diane',
        'Dylan','Ruth','Bruce','Julie','Wayne','Olivia','Elijah','Joyce','Randy','Virginia',
        'Johnny','Victoria','Tyler','Kelly','Jose','Lauren','Adam','Christina','Nathan','Joan',
        'Henry','Evelyn','Douglas','Judith','Zachary','Megan','Peter','Andrea','Kyle','Cheryl',
        'Noah','Hannah','Ethan','Jacqueline','Jeremy','Martha','Walter','Gloria','Christian','Teresa',
        'Keith','Ann','Roger','Sara','Terry','Madison','Austin','Frances','Sean','Kathryn',
        'Gerald','Janice','Carl','Jean','Harold','Abigail','Dylan','Alice','Arthur','Judy',
        'Lawrence','Sophia','Jordan','Grace','Jesse','Denise','Bryan','Amber','Billy','Doris',
        'Bruce','Marilyn','Gabriel','Danielle','Joe','Beverly','Logan','Isabella','Albert','Theresa',
        'Willie','Diana','Alan','Natalie','Eugene','Brittany','Russell','Charlotte','Vincent','Marie',
        'Philip','Kayla','Bobby','Alexis','Johnny','Lori','Bradley','Linda','Roy','Rosa',
        'Elijah','Alyssa','Randy','James','Wayne','Anna','Howard','Samantha','Dylan','Katherine',
        'Tyler','Christine','Jose','Debra','Adam','Janet','Nathan','Catherine','Henry','Maria',
        'Douglas','Heather','Zachary','Diane','Peter','Ruth','Kyle','Julie','Noah','Olivia',
        'Ethan','Joyce','Jeremy','Virginia','Walter','Victoria','Christian','Kelly','Keith','Lauren',
        'Roger','Christina','Terry','Joan','Austin','Evelyn','Sean','Judith','Gerald','Megan',
        'Carl','Andrea','Harold','Cheryl','Dylan','Hannah','Arthur','Jacqueline','Lawrence','Martha',
        'Jordan','Gloria','Jesse','Teresa','Bryan','Ann','Billy','Sara','Bruce','Madison',
        'Gabriel','Frances','Joe','Kathryn','Logan','Janice','Albert','Jean','Willie','Abigail',
        'Alan','Alice','Eugene','Judy','Russell','Sophia','Vincent','Grace','Philip','Denise',
        'Bobby','Amber','Johnny','Doris','Bradley','Marilyn','Roy','Danielle','Elijah','Beverly',
        'Randy','Isabella','Wayne','Theresa','Howard','Diana','Dylan','Natalie','Tyler','Brittany',
        'Jose','Charlotte','Adam','Marie','Nathan','Kayla','Henry','Alexis','Douglas','Lori',
        'Zachary','Linda','Peter','Rosa','Kyle','Alyssa','Noah','James','Ethan','Anna',
        'Jeremy','Samantha','Walter','Katherine','Christian','Christine','Keith','Debra','Roger','Janet',
        'Terry','Catherine','Austin','Maria','Sean','Heather','Gerald','Diane','Carl','Ruth',
        'Harold','Julie','Dylan','Olivia','Arthur','Joyce','Lawrence','Virginia','Jordan','Victoria',
        'Jesse','Kelly','Bryan','Lauren','Billy','Christina','Bruce','Joan','Gabriel','Evelyn',
        'Joe','Judith','Logan','Megan','Albert','Andrea','Willie','Cheryl','Alan','Hannah',
        'Eugene','Jacqueline','Russell','Martha','Vincent','Gloria','Philip','Teresa','Bobby','Ann',
        'Johnny','Sara','Bradley','Madison','Roy','Frances','Elijah','Kathryn','Randy','Janice',
        'Wayne','Jean','Howard','Abigail','Dylan','Alice','Tyler','Judy','Jose','Sophia',
        'Adam','Grace','Nathan','Denise','Henry','Amber','Douglas','Doris','Zachary','Marilyn',
        'Peter','Danielle','Kyle','Beverly','Noah','Isabella','Ethan','Theresa','Jeremy','Diana',
        'Walter','Natalie','Christian','Brittany','Keith','Charlotte','Roger','Marie','Terry','Kayla',
        'Austin','Alexis','Sean','Lori','Gerald','Linda','Carl','Rosa','Harold','Alyssa',
        'Dylan','James','Arthur','Anna','Lawrence','Samantha','Jordan','Katherine','Jesse','Christine',
        'Bryan','Debra','Billy','Janet','Bruce','Catherine','Gabriel','Maria','Joe','Heather',
        'Logan','Diane','Albert','Ruth','Willie','Julie','Alan','Olivia','Eugene','Joyce',
        'Russell','Virginia','Vincent','Victoria','Philip','Kelly','Bobby','Lauren','Johnny','Christina',
        'Bradley','Joan','Roy','Evelyn','Elijah','Judith','Randy','Megan','Wayne','Andrea',
        'Howard','Cheryl','Dylan','Hannah','Tyler','Jacqueline','Jose','Martha','Adam','Gloria',
        'Nathan','Teresa','Henry','Ann','Douglas','Sara','Zachary','Madison','Peter','Frances',
        'Kyle','Kathryn','Noah','Janice','Ethan','Jean','Jeremy','Abigail','Walter','Alice',
        'Christian','Judy','Keith','Sophia','Roger','Grace','Terry','Denise','Austin','Amber',
        'Sean','Doris','Gerald','Marilyn','Carl','Danielle','Harold','Beverly','Dylan','Isabella',
        'Arthur','Theresa','Lawrence','Diana','Jordan','Natalie','Jesse','Brittany','Bryan','Charlotte',
        'Billy','Marie','Bruce','Kayla','Gabriel','Alexis','Joe','Lori','Logan','Linda',
        'Albert','Rosa','Willie','Alyssa','Alan','James','Eugene','Anna','Russell','Samantha',
        'Vincent','Katherine','Philip','Christine','Bobby','Debra','Johnny','Janet','Bradley','Catherine',
        'Roy','Maria','Elijah','Heather','Randy','Diane','Wayne','Ruth','Howard','Julie',
        'Dylan','Olivia','Tyler','Joyce','Jose','Virginia','Adam','Victoria','Nathan','Kelly',
        'Henry','Lauren','Douglas','Christina','Zachary','Joan','Peter','Evelyn','Kyle','Judith',
        'Noah','Megan','Ethan','Andrea','Jeremy','Cheryl','Walter','Hannah','Christian','Jacqueline',
        'Keith','Martha','Roger','Gloria','Terry','Teresa','Austin','Ann','Sean','Sara',
        'Gerald','Madison','Carl','Frances','Harold','Kathryn','Dylan','Janice','Arthur','Jean',
        'Lawrence','Abigail','Jordan','Alice','Jesse','Judy','Bryan','Sophia','Billy','Grace',
        'Bruce','Denise','Gabriel','Amber','Joe','Doris','Logan','Marilyn','Albert','Danielle',
        'Willie','Beverly','Alan','Isabella','Eugene','Theresa','Russell','Diana','Vincent','Natalie',
        'Philip','Brittany','Bobby','Charlotte','Johnny','Marie','Bradley','Kayla','Roy','Alexis',
        'Elijah','Lori','Randy','Linda','Wayne','Rosa','Howard','Alyssa','Dylan','James',
        'Tyler','Anna','Jose','Samantha','Adam','Katherine','Nathan','Christine','Henry','Debra',
        'Douglas','Janet','Zachary','Catherine','Peter','Maria','Kyle','Heather','Noah','Diane',
        'Ethan','Ruth','Jeremy','Julie','Walter','Olivia','Christian','Joyce','Keith','Virginia',
        'Roger','Victoria','Terry','Kelly','Austin','Lauren','Sean','Christina','Gerald','Joan',
        'Carl','Evelyn','Harold','Judith','Dylan','Megan','Arthur','Andrea','Lawrence','Cheryl',
        'Jordan','Hannah','Jesse','Jacqueline','Bryan','Martha','Billy','Gloria','Bruce','Teresa',
        'Gabriel','Ann','Joe','Sara','Logan','Madison','Albert','Frances','Willie','Kathryn',
        'Alan','Janice','Eugene','Jean','Russell','Abigail','Vincent','Alice','Philip','Judy',
        'Bobby','Sophia','Johnny','Grace','Bradley','Denise','Roy','Amber','Elijah','Doris',
        'Randy','Marilyn','Wayne','Danielle','Howard','Beverly','Dylan','Isabella','Tyler','Theresa',
        'Jose','Diana','Adam','Natalie','Nathan','Brittany','Henry','Charlotte','Douglas','Marie',
        'Zachary','Kayla','Peter','Alexis','Kyle','Lori','Noah','Linda','Ethan','Rosa',
        'Jeremy','Alyssa','Walter','James','Christian','Anna','Keith','Samantha','Roger','Katherine',
        'Terry','Christine','Austin','Debra','Sean','Janet','Gerald','Catherine','Carl','Maria',
        'Harold','Heather','Dylan','Diane','Arthur','Ruth','Lawrence','Julie','Jordan','Olivia',
        'Jesse','Joyce','Bryan','Virginia','Billy','Victoria','Bruce','Kelly','Gabriel','Lauren',
        'Joe','Christina','Logan','Joan','Albert','Evelyn','Willie','Judith','Alan','Megan',
        'Eugene','Andrea','Russell','Cheryl','Vincent','Hannah','Philip','Jacqueline','Bobby','Martha',
        'Johnny','Gloria','Bradley','Teresa','Roy','Ann','Elijah','Sara','Randy','Madison',
        'Wayne','Frances','Howard','Kathryn','Dylan','Janice','Tyler','Jean','Jose','Abigail',
        'Adam','Alice','Nathan','Judy','Henry','Sophia','Douglas','Grace','Zachary','Denise',
        'Peter','Amber','Kyle','Doris','Noah','Marilyn','Ethan','Danielle','Jeremy','Beverly',
        'Walter','Isabella','Christian','Theresa','Keith','Diana','Roger','Natalie','Terry','Brittany',
        'Austin','Charlotte','Sean','Marie','Gerald','Kayla','Carl','Alexis','Harold','Lori',
        'Dylan','Linda','Arthur','Rosa','Lawrence','Alyssa','Jordan','James','Jesse','Anna',
        'Bryan','Samantha','Billy','Katherine','Bruce','Christine','Gabriel','Debra','Joe','Janet',
        'Logan','Catherine','Albert','Maria','Willie','Heather','Alan','Diane','Eugene','Ruth',
        'Russell','Julie','Vincent','Olivia','Philip','Joyce','Bobby','Virginia','Johnny','Victoria',
        'Bradley','Kelly','Roy','Lauren','Elijah','Christina','Randy','Joan','Wayne','Evelyn',
        'Howard','Judith','Dylan','Megan','Tyler','Andrea','Jose','Cheryl','Adam','Hannah',
        'Nathan','Jacqueline','Henry','Martha','Douglas','Gloria','Zachary','Teresa','Peter','Ann',
        'Kyle','Sara','Noah','Madison','Ethan','Frances','Jeremy','Kathryn','Walter','Janice',
        'Christian','Jean','Keith','Abigail','Roger','Alice','Terry','Judy','Austin','Sophia',
        'Sean','Grace','Gerald','Denise','Carl','Amber','Harold','Doris','Dylan','Marilyn',
        'Arthur','Danielle','Lawrence','Beverly','Jordan','Isabella','Jesse','Theresa','Bryan','Diana',
        'Billy','Natalie','Bruce','Brittany','Gabriel','Charlotte','Joe','Marie','Logan','Kayla',
        'Albert','Alexis','Willie','Lori','Alan','Linda','Eugene','Rosa','Russell','Alyssa',
        'Vincent','James','Philip','Anna','Bobby','Samantha','Johnny','Katherine','Bradley','Christine',
        'Roy','Debra','Elijah','Janet','Randy','Catherine','Wayne','Maria','Howard','Heather',
        'Dylan','Diane','Tyler','Ruth','Jose','Julie','Adam','Olivia','Nathan','Joyce',
        'Henry','Virginia','Douglas','Victoria','Zachary','Kelly','Peter','Lauren','Kyle','Christina',
        'Noah','Joan','Ethan','Evelyn','Jeremy','Judith','Walter','Megan','Christian','Andrea',
        'Keith','Cheryl','Roger','Hannah','Terry','Jacqueline','Austin','Martha','Sean','Gloria',
        'Gerald','Teresa','Carl','Ann','Harold','Sara','Dylan','Madison','Arthur','Frances',
        'Lawrence','Kathryn','Jordan','Janice','Jesse','Jean','Bryan','Abigail','Billy','Alice',
        'Bruce','Judy','Gabriel','Sophia','Joe','Grace','Logan','Denise','Albert','Amber',
        'Willie','Doris','Alan','Marilyn','Eugene','Danielle','Russell','Beverly','Vincent','Isabella',
        'Philip','Theresa','Bobby','Diana','Johnny','Natalie','Bradley','Brittany','Roy','Charlotte',
        'Elijah','Marie','Randy','Kayla','Wayne','Alexis','Howard','Lori'
    ]
    last_names = [
        'Smith','Johnson','Williams','Brown','Jones','Garcia','Miller','Davis','Rodriguez','Martinez',
        'Hernandez','Lopez','Gonzalez','Wilson','Anderson','Thomas','Taylor','Moore','Jackson','Martin',
        'Lee','Perez','Thompson','White','Harris','Sanchez','Clark','Ramirez','Lewis','Robinson',
        'Walker','Young','Allen','King','Wright','Scott','Torres','Nguyen','Hill','Flores',
        'Green','Adams','Nelson','Baker','Hall','Rivera','Campbell','Mitchell','Carter','Roberts',
        'Gomez','Phillips','Evans','Turner','Diaz','Parker','Cruz','Edwards','Collins','Reyes',
        'Stewart','Morris','Morales','Murphy','Cook','Rogers','Gutierrez','Ortiz','Morgan','Cooper',
        'Peterson','Bailey','Reed','Kelly','Howard','Ramos','Kim','Cox','Ward','Richardson',
        'Watson','Brooks','Chavez','Wood','James','Bennett','Gray','Mendoza','Ruiz','Hughes',
        'Price','Alvarez','Castillo','Sanders','Patel','Myers','Long','Ross','Foster','Jimenez',
        'Powell','Jenkins','Perry','Russell','Sullivan','Bell','Coleman','Butler','Henderson','Barnes',
        'Gonzales','Fisher','Vasquez','Simmons','Patterson','Jordan','Reynolds','Hamilton','Graham','Wallace',
        'Woods','Cole','West','Jordan','Owens','Reynolds','Fisher','Ellis','Harrison','Gibson',
        'McDonald','Cruz','Marshall','Freeman','Wells','Webb','Simpson','Stevens','Tucker','Porter',
        'Hunter','Hicks','Crawford','Henry','Boyd','Mason','Morales','Kennedy','Warren','Dixon',
        'Ramos','Reeves','Burns','Gordon','Shaw','Holmes','Rice','Robertson','Hunt','Black',
        'Daniels','Palmer','Mills','Grant','Cunningham','Williamson','Carr','Perkins','Long','Ross',
        'Foster','Little','Stone','Hawkins','Dunn','Fox','Blake','Wagner','Spencer','Hayes',
        'Webb','Berry','Sanders','Barnes','Ross','Coleman','Jenkins','Perry','Bell','Butler',
        'Henderson','Gonzales','Fisher','Vasquez','Simmons','Patterson','Jordan','Reynolds','Hamilton','Graham',
        'Wallace','Woods','Cole','West','Jordan','Owens','Fisher','Ellis','Harrison','Gibson',
        'McDonald','Cruz','Marshall','Freeman','Wells','Webb','Simpson','Stevens','Tucker','Porter',
        'Hunter','Hicks','Crawford','Henry','Boyd','Mason','Morales','Kennedy','Warren','Dixon',
        'Ramos','Reeves','Burns','Gordon','Shaw','Holmes','Rice','Robertson','Hunt','Black',
        'Daniels','Palmer','Mills','Grant','Cunningham','Williamson','Carr','Perkins','Long','Ross',
        'Foster','Little','Stone','Hawkins','Dunn','Fox','Blake','Wagner','Spencer','Hayes',
        'Webb','Berry','Sanders','Barnes','Gordon','Mendoza','Ruiz','Hughes','Price','Alvarez',
        'Castillo','Sanders','Patel','Myers','Long','Ross','Foster','Jimenez','Powell','Jenkins',
        'Perry','Russell','Sullivan','Bell','Coleman','Butler','Henderson','Barnes','Gonzales','Fisher',
        'Vasquez','Simmons','Patterson','Jordan','Reynolds','Hamilton','Graham','Wallace','Woods','Cole',
        'West','Owens','Ellis','Harrison','Gibson','McDonald','Cruz','Marshall','Freeman','Wells',
        'Simpson','Stevens','Tucker','Porter','Hunter','Hicks','Crawford','Henry','Boyd','Mason',
        'Morales','Kennedy','Warren','Dixon','Ramos','Reeves','Burns','Gordon','Shaw','Holmes',
        'Rice','Robertson','Hunt','Black','Daniels','Palmer','Mills','Grant','Cunningham','Williamson',
        'Carr','Perkins','Little','Stone','Hawkins','Dunn','Fox','Blake','Wagner','Spencer',
        'Hayes','Berry','Campbell','Mitchell','Carter','Roberts','Gomez','Phillips','Evans','Turner',
        'Diaz','Parker','Cruz','Edwards','Collins','Reyes','Stewart','Morris','Morales','Murphy',
        'Cook','Rogers','Gutierrez','Ortiz','Morgan','Cooper','Peterson','Bailey','Reed','Kelly',
        'Howard','Ramos','Kim','Cox','Ward','Richardson','Watson','Brooks','Chavez','Wood',
        'James','Bennett','Gray','Mendoza','Ruiz','Hughes','Price','Alvarez','Castillo','Patel',
        'Myers','Jimenez','Powell','Jenkins','Perry','Russell','Sullivan','Coleman','Butler','Henderson',
        'Barnes','Gonzales','Fisher','Vasquez','Simmons','Patterson','Jordan','Reynolds','Hamilton','Graham',
        'Wallace','Woods','Cole','West','Owens','Ellis','Harrison','Gibson','McDonald','Cruz',
        'Marshall','Freeman','Wells','Simpson','Stevens','Tucker','Porter','Hunter','Hicks','Crawford',
        'Henry','Boyd','Mason','Morales','Kennedy','Warren','Dixon','Ramos','Reeves','Burns',
        'Gordon','Shaw','Holmes','Rice','Robertson','Hunt','Black','Daniels','Palmer','Mills',
        'Grant','Cunningham','Williamson','Carr','Perkins','Little','Stone','Hawkins','Dunn','Fox',
        'Blake','Wagner','Spencer','Hayes','Berry','Diaz','Parker','Edwards','Collins','Reyes',
        'Stewart','Morris','Murphy','Cook','Rogers','Gutierrez','Ortiz','Morgan','Cooper','Peterson',
        'Bailey','Reed','Kim','Cox','Ward','Richardson','Watson','Brooks','Chavez','Wood',
        'Bennett','Gray','Alvarez','Castillo','Patel','Myers','Jimenez','Powell','Perry','Russell',
        'Sullivan','Coleman','Butler','Henderson','Barnes','Gonzales','Fisher','Vasquez','Simmons','Patterson',
        'Jordan','Reynolds','Hamilton','Graham','Wallace','Woods','Cole','West','Owens','Ellis',
        'Harrison','Gibson','McDonald','Cruz','Marshall','Freeman','Wells','Simpson','Stevens','Tucker',
        'Porter','Hunter','Hicks','Crawford','Henry','Boyd','Mason','Morales','Kennedy','Warren',
        'Dixon','Ramos','Reeves','Burns','Gordon','Shaw','Holmes','Rice','Robertson','Hunt',
        'Black','Daniels','Palmer','Mills','Grant','Cunningham','Williamson','Carr','Perkins','Little',
        'Stone','Hawkins','Dunn','Fox','Blake','Wagner','Spencer','Hayes','Berry'
    ]
    return f"{random.choice(first_names)} {random.choice(last_names)}"

# ==================== DB ====================
def get_db():
    return sqlite3.connect("shop.db", timeout=15)

def init_db():
    conn = get_db()
    c = conn.cursor()
    c.execute('CREATE TABLE IF NOT EXISTS users (user_id INTEGER PRIMARY KEY, balance REAL DEFAULT 0.0)')
    c.execute('''CREATE TABLE IF NOT EXISTS countries (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        country_code TEXT NOT NULL,
        name TEXT,
        flag TEXT,
        provider_ids TEXT DEFAULT '',
        price REAL
    )''')
    c.execute('''CREATE TABLE IF NOT EXISTS orders (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        order_id TEXT UNIQUE,
        phone TEXT,
        country_name TEXT,
        price REAL,
        status TEXT DEFAULT 'WAITING',
        created_at INTEGER
    )''')
    conn.commit(); conn.close()

def get_balance(uid):
    conn = get_db()
    r = conn.execute('SELECT balance FROM users WHERE user_id=?', (uid,)).fetchone()
    if r:
        conn.close(); return r[0]
    conn.execute('INSERT OR IGNORE INTO users (user_id, balance) VALUES (?,0)', (uid,))
    conn.commit(); conn.close()
    return 0.0

def add_balance(uid, amt):
    conn = get_db()
    conn.execute('UPDATE users SET balance = balance + ? WHERE user_id = ?', (amt, uid))
    conn.commit(); conn.close()

def create_user(uid):
    conn = get_db()
    conn.execute('INSERT OR IGNORE INTO users (user_id, balance) VALUES (?,0)', (uid,))
    conn.commit(); conn.close()

def all_users():
    conn = get_db()
    rows = conn.execute('SELECT user_id, balance FROM users ORDER BY balance DESC').fetchall()
    conn.close(); return rows

init_db()

client = TelegramClient(MemorySession(), API_ID, API_HASH)
admin_states = {}
user_states = {}
auto_check_tasks = {}
PROCESSED_EVENTS = set()

def is_duplicate(evt_key):
    if evt_key in PROCESSED_EVENTS:
        return True
    PROCESSED_EVENTS.add(evt_key)
    if len(PROCESSED_EVENTS) > 10000:
        PROCESSED_EVENTS.clear()
    return False

# ==================== API ====================
async def api(action, **kw):
    p = {'api_key': SMSBOWER_API_KEY, 'action': action, **kw}
    try:
        async with aiohttp.ClientSession() as s:
            async with s.get(SMSBOWER_URL, params=p, timeout=aiohttp.ClientTimeout(total=15)) as r:
                res = await r.text()
                return res.strip() if res else 'ERROR'
    except Exception:
        return 'ERROR'

async def api_json(action, **kw):
    p = {'api_key': SMSBOWER_API_KEY, 'action': action, **kw}
    try:
        async with aiohttp.ClientSession() as s:
            async with s.get(SMSBOWER_URL, params=p, timeout=aiohttp.ClientTimeout(total=20)) as r:
                return await r.json(content_type=None)
    except Exception:
        return None

# ==================== COUNTRY DATA ====================
COUNTRY_FLAGS = {
    '0':'🇷🇺','1':'🇺🇦','2':'🇰🇿','4':'🇵🇭','5':'🇮🇩','6':'🇮🇳','7':'🇺🇸',
    '8':'🇬🇧','9':'🇨🇳','10':'🇧🇷','11':'🇵🇰','12':'🇳🇬','13':'🇧🇩','14':'🇪🇬','15':'🇻🇳',
    '16':'🇲🇽','17':'🇹🇷','18':'🇩🇪','19':'🇫🇷','20':'🇮🇹','21':'🇪🇸','22':'🇰🇷','23':'🇯🇵',
    '24':'🇨🇦','25':'🇦🇺','26':'🇸🇦','27':'🇦🇪','28':'🇮🇷','29':'🇮🇶','30':'🇹🇭','31':'🇲🇾',
    '32':'🇸🇬','33':'🇿🇦','34':'🇰🇪','35':'🇬🇭','36':'🇨🇴','37':'🇦🇷','38':'🇨🇱','39':'🇵🇪',
    '40':'🇵🇱','41':'🇷🇴','42':'🇨🇿','43':'🇭🇺','44':'🇸🇪','45':'🇳🇴','46':'🇩🇰','47':'🇫🇮',
    '48':'🇮🇪','49':'🇵🇹','50':'🇬🇷','51':'🇧🇬','52':'🇭🇷','53':'🇷🇸','55':'🇰🇬',
    '56':'🇹🇯','57':'🇦🇲','58':'🇬🇪','59':'🇲🇩','60':'🇧🇾','61':'🇱🇹','62':'🇱🇻','63':'🇪🇪',
    '64':'🇲🇲','65':'🇰🇭','66':'🇱🇦','67':'🇳🇵','68':'🇱🇰','69':'🇦🇫','70':'🇹🇳','71':'🇩🇿',
    '72':'🇲🇦','73':'🇱🇾','74':'🇸🇩','75':'🇪🇹','76':'🇹🇿','77':'🇺🇬','78':'🇿🇲','79':'🇿🇼',
    '80':'🇧🇼','81':'🇲🇿','82':'🇦🇴','83':'🇨🇮','84':'🇸🇳','85':'🇲🇱','86':'🇧🇫','87':'🇳🇪',
    '88':'🇹🇩','89':'🇨🇲','90':'🇬🇳','91':'🇬🇲','92':'🇱🇷','93':'🇸🇱','95':'🇷🇼',
    '96':'🇸🇸','97':'🇪🇷','98':'🇩🇯','99':'🇸🇴','100':'🇲🇬','101':'🇲🇺','103':'🇨🇻',
    '107':'🇦🇩','108':'🇲🇨','109':'🇱🇮','110':'🇸🇲','111':'🇲🇹','112':'🇨🇾','113':'🇮🇸',
    '114':'🇱🇺','115':'🇧🇪','116':'🇳🇱','117':'🇦🇹','118':'🇨🇭','119':'🇱🇧','120':'🇯🇴',
    '121':'🇸🇾','122':'🇮🇱','124':'🇾🇪','125':'🇴🇲','126':'🇰🇼','127':'🇧🇭','128':'🇶🇦',
    '129':'🇲🇻',
}
COUNTRY_NAMES = {
    '0':'Russia','1':'Ukraine','2':'Kazakhstan','4':'Philippines','5':'Indonesia',
    '6':'India','7':'USA','8':'UK','9':'China','10':'Brazil','11':'Pakistan','12':'Nigeria',
    '13':'Bangladesh','14':'Egypt','15':'Vietnam','16':'Mexico','17':'Turkey','18':'Germany',
    '19':'France','20':'Italy','21':'Spain','22':'South Korea','23':'Japan','24':'Canada',
    '25':'Australia','26':'Saudi Arabia','27':'UAE','28':'Iran','29':'Iraq','30':'Thailand',
    '31':'Malaysia','32':'Singapore','33':'South Africa','34':'Kenya','35':'Ghana','36':'Colombia',
    '37':'Argentina','38':'Chile','39':'Peru','40':'Poland','41':'Romania','42':'Czech',
    '43':'Hungary','44':'Sweden','45':'Norway','46':'Denmark','47':'Finland','48':'Ireland',
    '49':'Portugal','50':'Greece','51':'Bulgaria','52':'Croatia','53':'Serbia','55':'Kyrgyzstan',
    '56':'Tajikistan','57':'Armenia','58':'Georgia','59':'Moldova','60':'Belarus','61':'Lithuania',
    '62':'Latvia','63':'Estonia','64':'Myanmar','65':'Cambodia','66':'Laos','67':'Nepal',
    '68':'Sri Lanka','69':'Afghanistan','70':'Tunisia','71':'Algeria','72':'Morocco','73':'Libya',
    '74':'Sudan','75':'Ethiopia','76':'Tanzania','77':'Uganda','78':'Zambia','79':'Zimbabwe',
    '80':'Botswana','81':'Mozambique','82':'Angola','83':'Ivory Coast','84':'Senegal','85':'Mali',
    '86':'Burkina Faso','87':'Niger','88':'Chad','89':'Cameroon','90':'Guinea','91':'Gambia',
    '92':'Liberia','93':'Sierra Leone','95':'Rwanda','96':'South Sudan','97':'Eritrea','98':'Djibouti',
    '99':'Somalia','100':'Madagascar','101':'Mauritius','103':'Cape Verde','107':'Andorra',
    '108':'Monaco','109':'Liechtenstein','110':'San Marino','111':'Malta','112':'Cyprus',
    '113':'Iceland','114':'Luxembourg','115':'Belgium','116':'Netherlands','117':'Austria',
    '118':'Switzerland','119':'Lebanon','120':'Jordan','121':'Syria','122':'Israel','124':'Yemen',
    '125':'Oman','126':'Kuwait','127':'Bahrain','128':'Qatar','129':'Maldives',
}

# ==================== BUTTONS ====================
def main_buttons(uid):
    btns = [
        [Button.inline("🛒 Buy Telegram", b"buy_tg"), Button.inline("👤 Account", b"my_account")],
        [Button.inline("📋 Active Orders", b"active_orders")]
    ]
    if uid == ADMIN_ID:
        btns.append([Button.inline("⚙️ Admin Panel", b"admin_panel")])
    return btns

def main_text(uid):
    bal = get_balance(uid)
    return f"👋 **Welcome!**\n\n💳 Balance: **${bal:.2f}**\n⚡ Service: **Telegram**\n\nChoose:"

def admin_buttons():
    return [
        [Button.inline("➕ Add Country", b"adm_add_c"), Button.inline("📋 Countries", b"adm_list_c")],
        [Button.inline("➕ Add Balance", b"adm_add_b"), Button.inline("➖ Sub Balance", b"adm_sub_b")],
        [Button.inline("👥 User Balances", b"adm_balances")],
        [Button.inline("🏷️ View Providers", b"adm_providers")],
        [Button.inline("🔙 Main Menu", b"back_main")]
    ]

# ==================== RETRY GET NUMBER ====================
async def retry_get_number(c_code, provider_ids, max_retries=10, delay=2):
    """Try multiple times to get a number from the API"""
    params = {'service': 'tg', 'country': c_code}
    if provider_ids:
        params['providerIds'] = provider_ids
    for attempt in range(max_retries):
        res = await api('getNumber', **params)
        if res.startswith('ACCESS_NUMBER'):
            parts = res.split(':')
            return True, parts[1], parts[2]
        if attempt < max_retries - 1:
            await asyncio.sleep(delay)
    return False, None, None

# ==================== AUTO CHECK SMS ====================
async def auto_check_sms(uid, order_id, phone_display):
    try:
        for _ in range(120):
            await asyncio.sleep(3)
            conn = get_db()
            r = conn.execute('SELECT status FROM orders WHERE order_id=?', (order_id,)).fetchone()
            conn.close()
            if not r or r[0] != 'WAITING':
                return

            status = await api('getStatus', id=order_id)
            if status.startswith('STATUS_OK'):
                parts = status.split(':')
                code = parts[1] if len(parts) > 1 else 'RECEIVED'
                await api('setStatus', id=order_id, status='6')

                conn = get_db()
                conn.execute("UPDATE orders SET status='COMPLETED' WHERE order_id=?", (order_id,))
                conn.commit(); conn.close()
                auto_check_tasks.pop(order_id, None)

                # Get fake name for display
                fake_name = await get_fake_name()
                try:
                    await client.send_message(uid,
                        f"🎉 **Code Received!**\n\n"
                        f"📱 Phone: `{phone_display}`\n"
                        f"👤 Name: `{fake_name}`\n"
                        f"🔑 Code: `{code}`\n\n✅ Done!",
                        buttons=[[Button.inline("📋 Active Orders", b"active_orders")], [Button.inline("🔙 Menu", b"back_main")]])
                except: pass
                return

            elif status.startswith('STATUS_CANCEL'):
                conn = get_db()
                row = conn.execute("SELECT price, status FROM orders WHERE order_id=?", (order_id,)).fetchone()
                if row and row[1] == 'WAITING':
                    conn.execute("UPDATE orders SET status='CANCELLED' WHERE order_id=?", (order_id,))
                    conn.commit()
                    add_balance(uid, row[0])
                    try:
                        await client.send_message(uid,
                            f"❌ **Order Expired/Cancelled**\n📱 `{phone_display}`\n💵 ${row[0]:.2f} refunded.",
                            buttons=[[Button.inline("🔙 Menu", b"back_main")]])
                    except: pass
                conn.close()
                auto_check_tasks.pop(order_id, None)
                return
    except asyncio.CancelledError:
        pass
    except Exception as e:
        print(f"Auto check error: {e}")

# ==================== BATCH BUY ====================
async def process_batch_purchase(event, uid, cid, count):
    conn = get_db()
    row = conn.execute("SELECT country_code, name, flag, provider_ids, price FROM countries WHERE id=?", (cid,)).fetchone()
    if not row:
        conn.close(); await event.respond("❌ Country not found."); return
    c_code, name, flag, provider_ids, price = row
    total_cost = price * count

    bal_row = conn.execute("SELECT balance FROM users WHERE user_id=?", (uid,)).fetchone()
    bal = bal_row[0] if bal_row else 0.0
    conn.close()

    if bal < total_cost:
        await event.respond(f"❌ Need **${total_cost:.2f}** (You have **${bal:.2f}**)")
        return

    progress_msg = await event.respond(f"⏳ Ordering {count}x {flag} {name}...")

    successful = 0
    created_orders = []

    for i in range(count):
        # Retry for 60 seconds per number
        got = False
        t0 = time.time()
        while time.time() - t0 < 60:
            params = {'service': 'tg', 'country': c_code}
            if provider_ids:
                params['providerIds'] = provider_ids
            res = await api('getNumber', **params)
            if res.startswith('ACCESS_NUMBER'):
                parts = res.split(':')
                order_id, phone = parts[1], parts[2]
                if len(phone) > 7:
                    masked = phone[:3] + '*' * (len(phone) - 7) + phone[-4:]
                else:
                    masked = phone
                phone_display = f"+{masked}"
                add_balance(uid, -price)
                conn = get_db()
                conn.execute(
                    "INSERT INTO orders (user_id, order_id, phone, country_name, price, status, created_at) VALUES (?,?,?,?,?,'WAITING',?)",
                    (uid, order_id, phone_display, name, price, int(time.time())))
                conn.commit(); conn.close()
                task = asyncio.create_task(auto_check_sms(uid, order_id, phone_display))
                auto_check_tasks[order_id] = task
                successful += 1
                created_orders.append((order_id, phone_display))
                got = True
                break
            await asyncio.sleep(3)
        if not got:
            break
        await asyncio.sleep(0.5)

    if successful == 0:
        await progress_msg.edit(
            f"⚠️ No numbers available for {flag} {name}.",
            buttons=[[Button.inline("🔄 Retry", f"buy_c_{cid}".encode())], [Button.inline("🔙 Back", b"back_main")]])
        return

    lines = [f"📱 `{p}` (ID: `{o}`)" for o, p in created_orders]
    summary = (
        f"✅ **{successful}/{count} Numbers!**\n\n"
        f"🌍 {flag} **{name}**\n💵 Deducted: **${(successful * price):.2f}**\n\n"
        + "\n".join(lines) + "\n\n⏳ Auto-checking SMS...")
    await progress_msg.edit(summary, buttons=[
        [Button.inline("📋 Active Orders", b"active_orders")],
        [Button.inline("❌ Cancel All", b"cnc_all")]])

# ==================== START ====================
@client.on(events.NewMessage(pattern=r'^/start$', incoming=True, func=lambda e: e.is_private))
async def cmd_start(event):
    if is_duplicate(f"start_{event.id}"): return
    uid = event.sender_id
    create_user(uid)
    user_states.pop(uid, None)
    user = await event.get_sender()
    name = user.first_name if user and user.first_name else "User"
    bal = get_balance(uid)
    await event.respond(
        f"👋 **Hello {name}!**\n\n💳 Balance: **${bal:.2f}**\n⚡ Service: **Telegram**\n\nChoose:",
        buttons=main_buttons(uid))

# ==================== CALLBACK ROUTER ====================
@client.on(events.CallbackQuery)
async def callback_router(event):
    query_id = getattr(event.query, 'id', None)
    if query_id and is_duplicate(f"q_{query_id}"):
        await event.answer(); return

    uid = event.sender_id
    try: data = event.data.decode()
    except: await event.answer(); return

    try:
        if data == "back_main":
            admin_states.pop(uid, None); user_states.pop(uid, None)
            await event.edit(main_text(uid), buttons=main_buttons(uid))

        elif data == "my_account":
            bal = get_balance(uid)
            await event.edit(f"👤 **Account**\n\n🆔 `{uid}`\n💰 **${bal:.2f}**",
                buttons=[[Button.inline("🔙 Back", b"back_main")]])

        elif data == "buy_tg":
            conn = get_db()
            rows = conn.execute("SELECT id, name, flag, country_code, price, provider_ids FROM countries ORDER BY name, price").fetchall()
            conn.close()
            if not rows:
                await event.answer("⚠️ No countries.", alert=True); return
            # Group by country code
            groups = {}
            for cid, name, flag, ccode, price, prov in rows:
                key = f"{flag}_{ccode}"
                if key not in groups:
                    groups[key] = {'flag': flag, 'name': name, 'code': ccode, 'items': []}
                groups[key]['items'].append({'id': cid, 'price': price, 'prov': prov})
            txt = "🌍 **Select Country:**\n\n"
            btns = []
            for key, g in groups.items():
                if len(g['items']) == 1:
                    item = g['items'][0]
                    txt += f"{g['flag']} {g['name']} — **${item['price']:.2f}**\n"
                    btns.append([Button.inline(f"{g['flag']} {g['name']} — ${item['price']:.2f}", f"buy_c_{item['id']}".encode())])
                else:
                    txt += f"{g['flag']} **{g['name']}**\n"
                    for item in g['items']:
                        prov_label = f" 🏷️{item['prov']}" if item['prov'] else ""
                        txt += f"  ✅ ${item['price']:.2f}{prov_label}\n"
                        btns.append([Button.inline(f"  ✅ {g['flag']} {g['name']} — ${item['price']:.2f}{prov_label}", f"buy_c_{item['id']}".encode())])
            btns.append([Button.inline("🔙 Back", b"back_main")])
            await event.edit(txt[:3900], buttons=btns)

        elif data.startswith("buy_c_"):
            cid = data.split("_")[2]
            conn = get_db()
            row = conn.execute("SELECT name, flag, price FROM countries WHERE id=?", (cid,)).fetchone()
            conn.close()
            if not row:
                await event.answer("Not found", alert=True); return
            name, flag, price = row
            btns = [
                [Button.inline("1x", f"qty_{cid}_1".encode()), Button.inline("2x", f"qty_{cid}_2".encode()), Button.inline("3x", f"qty_{cid}_3".encode())],
                [Button.inline("5x", f"qty_{cid}_5".encode()), Button.inline("✏️ Custom", f"custom_qty_{cid}".encode())],
                [Button.inline("🔙 Back", b"buy_tg")]]
            await event.edit(f"🌍 **{flag} {name}**\n💵 Price: **${price:.2f}**\n\nQuantity:", buttons=btns)

        elif data.startswith("qty_"):
            parts = data.split("_")
            cid, qty = parts[1], int(parts[2])
            await event.answer()
            await process_batch_purchase(event, uid, cid, qty)

        elif data.startswith("custom_qty_"):
            cid = data.split("_")[2]
            user_states[uid] = {"step": "custom_qty", "cid": cid}
            await event.edit("✏️ Send quantity (1-50):", buttons=[[Button.inline("🔙 Cancel", b"buy_tg")]])

        elif data.startswith("chk_sms_"):
            order_id = data.split("_")[2]
            conn = get_db()
            row = conn.execute("SELECT status, phone FROM orders WHERE order_id=?", (order_id,)).fetchone()
            conn.close()
            if not row:
                await event.answer("Not found", alert=True); return
            status = await api('getStatus', id=order_id)
            if status.startswith('STATUS_OK'):
                parts = status.split(':')
                code = parts[1] if len(parts) > 1 else 'RECEIVED'
                await api('setStatus', id=order_id, status='6')
                conn = get_db()
                conn.execute("UPDATE orders SET status='COMPLETED' WHERE order_id=?", (order_id,))
                conn.commit(); conn.close()
                if order_id in auto_check_tasks:
                    auto_check_tasks[order_id].cancel(); del auto_check_tasks[order_id]
                fake_name = await get_fake_name()
                await event.respond(
                    f"🎉 **Code Received!**\n\n📱 `{row[1]}`\n👤 Name: `{fake_name}`\n🔑 Code: `{code}`\n\n✅ Done!",
                    buttons=[[Button.inline("📋 Active Orders", b"active_orders")], [Button.inline("🔙 Menu", b"back_main")]])
            elif status == 'STATUS_WAIT_CODE':
                await event.answer("⏳ Waiting...", alert=True)
            elif status == 'STATUS_CANCEL':
                await event.answer("❌ Expired", alert=True)
            else:
                await event.answer(f"{status[:50]}", alert=True)

        elif data.startswith("cnc_ord_"):
            order_id = data.split("_")[2]
            conn = get_db()
            row = conn.execute("SELECT price, status FROM orders WHERE order_id=? AND user_id=?", (order_id, uid)).fetchone()
            if not row or row[1] != 'WAITING':
                conn.close(); await event.answer("❌ Cannot cancel", alert=True); return
            if order_id in auto_check_tasks:
                auto_check_tasks[order_id].cancel(); del auto_check_tasks[order_id]
            res = await api('setStatus', id=order_id, status='8')
            if any(x in res for x in ['ACCESS_CANCEL', 'ACCESS_OK', 'STATUS_CANCEL', 'CANCEL']):
                conn.execute("UPDATE orders SET status='CANCELLED' WHERE order_id=?", (order_id,))
                conn.commit(); conn.close()
                add_balance(uid, row[0])
                await event.answer(f"✅ Refunded ${row[0]:.2f}", alert=True)
                await show_active_orders(event, uid)
            else:
                conn.close(); await event.answer(f"❌ {res[:50]}", alert=True)

        elif data == "cnc_all":
            conn = get_db()
            active = conn.execute("SELECT order_id, price FROM orders WHERE user_id=? AND status='WAITING'", (uid,)).fetchall()
            conn.close()
            if not active:
                await event.answer("No active orders.", alert=True); return
            total = 0.0; cnt = 0
            for oid, price in active:
                if oid in auto_check_tasks:
                    auto_check_tasks[oid].cancel(); del auto_check_tasks[oid]
                res = await api('setStatus', id=oid, status='8')
                if any(x in res for x in ['ACCESS_CANCEL', 'ACCESS_OK', 'CANCEL']):
                    conn2 = get_db()
                    conn2.execute("UPDATE orders SET status='CANCELLED' WHERE order_id=?", (oid,))
                    conn2.commit(); conn2.close()
                    total += price; cnt += 1
                await asyncio.sleep(0.3)
            add_balance(uid, total)
            await event.edit(f"✅ **{cnt} Cancelled!**\n💵 Refunded: **${total:.2f}**\n\n{main_text(uid)}",
                buttons=main_buttons(uid))

        elif data == "active_orders":
            await show_active_orders(event, uid)

        # ==================== ADMIN ====================
        elif data == "admin_panel" and uid == ADMIN_ID:
            admin_states.pop(uid, None)
            await event.edit("⚙️ **Admin Panel**", buttons=admin_buttons())

        elif data == "adm_add_c" and uid == ADMIN_ID:
            admin_states[uid] = {"step": 1, "data": {}}
            await event.edit("**Step 1:** Country code\n(e.g. `0` = Russia, `7` = USA)",
                buttons=[[Button.inline("🔙 Cancel", b"admin_panel")]])

        elif data == "adm_list_c" and uid == ADMIN_ID:
            conn = get_db()
            rows = conn.execute("SELECT id, name, flag, country_code, price, provider_ids FROM countries").fetchall()
            conn.close()
            if not rows:
                await event.answer("No countries.", alert=True); return
            txt = "🌍 **Countries:**\n\n"
            btns = []
            for cid, name, flag, code, price, prov in rows[:30]:
                p = f" 🏷️{prov}" if prov else ""
                txt += f"{flag} {name} (`{code}`) | ${price:.2f}{p}\n"
                btns.append([Button.inline(f"🗑️ {flag} {name}", f"del_c_{cid}".encode())])
            btns.append([Button.inline("🔙 Back", b"admin_panel")])
            await event.edit(txt[:3900], buttons=btns)

        elif data.startswith("del_c_") and uid == ADMIN_ID:
            cid = data.split("_")[2]
            conn = get_db()
            conn.execute("DELETE FROM countries WHERE id=?", (cid,))
            conn.commit(); conn.close()
            await event.answer("✅ Deleted!")
            await event.edit("⚙️ **Admin Panel**", buttons=admin_buttons())

        elif data in ["adm_add_b", "adm_sub_b"] and uid == ADMIN_ID:
            is_add = (data == "adm_add_b")
            admin_states[uid] = {"step": "balance", "is_add": is_add}
            await event.edit(f"**{'Add' if is_add else 'Sub'} Balance**\n\nSend: `user_id amount`",
                buttons=[[Button.inline("🔙 Cancel", b"admin_panel")]])

        elif data == "adm_balances" and uid == ADMIN_ID:
            users = all_users()
            if not users:
                await event.answer("No users.", alert=True); return
            txt = "👥 **User Balances:**\n\n"
            for uid2, bal in users[:50]:
                txt += f"🆔 `{uid2}` — **${bal:.2f}**\n"
            btns = [[Button.inline("🔙 Back", b"admin_panel")]]
            await event.edit(txt[:3900], buttons=btns)

        elif data == "adm_providers" and uid == ADMIN_ID:
            await event.edit("⏳ **Fetching providers...**")
            data_api = await api_json('getTopCountriesByService', service='tg')
            if not data_api:
                await event.edit("❌ API error", buttons=[[Button.inline("🔙 Back", b"admin_panel")]])
                return
            txt = "🏷️ **Top Providers (Telegram):**\n\n"
            for ccode, providers in list(data_api.items())[:20]:
                flag = COUNTRY_FLAGS.get(str(ccode), '🌍')
                name = COUNTRY_NAMES.get(str(ccode), f'#{ccode}')
                txt += f"{flag} **{name}:**\n"
                for pid, info in list(providers.items())[:5]:
                    price = info.get('price', 0)
                    count = info.get('count', 0)
                    txt += f"  🏷️ `{pid}` | ${price} | {count} pcs\n"
                txt += "\n"
            btns = [[Button.inline("🔙 Back", b"admin_panel")]]
            await event.edit(txt[:3900], buttons=btns)

    except MessageNotModifiedError:
        pass
    except Exception as e:
        print(f"Callback Error: {e}")

async def show_active_orders(event, uid):
    conn = get_db()
    rows = conn.execute("SELECT order_id, phone, country_name FROM orders WHERE user_id=? AND status='WAITING'", (uid,)).fetchall()
    conn.close()
    if not rows:
        await event.edit("📋 No active orders.", buttons=[[Button.inline("🔙 Menu", b"back_main")]]); return
    btns = []
    for oid, phone, cname in rows:
        btns.append([Button.inline(f"📱 {phone} ({cname})", f"chk_sms_{oid}".encode()),
                     Button.inline("❌ Cancel", f"cnc_ord_{oid}".encode())])
    btns.append([Button.inline("❌ Cancel All", b"cnc_all")])
    btns.append([Button.inline("🔙 Menu", b"back_main")])
    await event.edit("📋 **Active Orders:**", buttons=btns)

# ==================== TEXT INPUT ====================
@client.on(events.NewMessage(incoming=True, func=lambda e: e.is_private and not e.text.startswith('/')))
async def msg_handler(event):
    if is_duplicate(f"msg_{event.id}"): return
    uid = event.sender_id
    text = event.raw_text.strip()

    if uid in user_states and user_states[uid].get("step") == "custom_qty":
        cid = user_states[uid].get("cid")
        user_states.pop(uid, None)
        try:
            qty = int(text)
            if qty < 1 or qty > 50:
                await event.respond("❌ 1-50"); return
            await process_batch_purchase(event, uid, cid, qty)
        except: await event.respond("❌ Send a number")
        return

    if uid != ADMIN_ID or uid not in admin_states:
        return

    state = admin_states[uid]
    step = state.get("step")

    if step == 1:
        state["data"]["code"] = text; state["step"] = 2
        await event.respond("**Step 2:** Country name")
    elif step == 2:
        state["data"]["name"] = text; state["step"] = 3
        await event.respond("**Step 3:** Flag emoji")
    elif step == 3:
        state["data"]["flag"] = text; state["step"] = 4
        await event.respond("**Step 4:** Provider IDs\n(e.g. `3193` or `0` for all)")
    elif step == 4:
        state["data"]["provider"] = "" if text == "0" else text; state["step"] = 5
        await event.respond("**Step 5:** Sell price ($)")
    elif step == 5:
        try:
            price = float(text)
            d = state["data"]
            conn = get_db()
            # Allow duplicate countries with same code (different providers)
            conn.execute(
                "INSERT INTO countries (country_code, name, flag, provider_ids, price) VALUES (?,?,?,?,?)",
                (d["code"], d["name"], d["flag"], d["provider"], price))
            conn.commit(); conn.close()
            prov = f" 🏷️{d['provider']}" if d['provider'] else ""
            del admin_states[uid]
            await event.respond(f"✅ **Added!**\n{d['flag']} {d['name']} | ${price:.2f}{prov}",
                buttons=admin_buttons())
        except ValueError:
            await event.respond("❌ Send a valid price:")
    elif step == "balance":
        try:
            parts = text.split()
            tid, amt = int(parts[0]), float(parts[1])
            if not state["is_add"]: amt = -amt
            create_user(tid); add_balance(tid, amt)
            del admin_states[uid]
            sign = "+" if state["is_add"] else "-"
            await event.respond(f"✅ `{tid}` {sign}${abs(amt):.2f}", buttons=admin_buttons())
        except: await event.respond("❌ Format: `user_id amount`")

# ==================== RUN ====================
async def main():
    print("🤖 Starting bot...")
    await client.start(bot_token=BOT_TOKEN)
    print("✅ Ready!")
    await client.run_until_disconnected()

if __name__ == "__main__":
    asyncio.run(main())
