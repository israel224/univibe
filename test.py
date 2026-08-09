from supabase import create_client, Client
import flet as ft
import os
import sys
import uuid
import mimetypes
import asyncio
import urllib.parse
from datetime import datetime, timezone

# --- VIDEO PLAYBACK ---
# In Flet 0.70+ the Video control was split out of core `flet` into the
# separate `flet-video` package (same pattern as flet-audio, flet-webview,
# etc.) — it's no longer available as ft.Video. Import it here, once, and
# fail over to None (not a crash) if the package isn't installed yet, so
# build_inline_video_player() below can degrade gracefully instead of the
# whole app breaking on startup.
#
#     pip install flet-video
#
try:
    import flet_video as ftv
except ImportError:
    ftv = None

# --- LIVE DATABASE CONNECTION ---
SUPABASE_URL = "https://vjvynztrznvlhxqatcsi.supabase.co"
SUPABASE_KEY = "sb_publishable_CGotNkzRyXY-P7klDoCysw_hFoo-8rq"
# NOTE: the actual `supabase` client is created per-session, inside main()
# below — not here. A client created here would be a single object shared
# by every browser tab/user connected to the running server process, and
# supabase.postgrest.auth(token) (called on login) mutates that shared
# object's auth header. With one client for everyone, whoever logs in most
# recently silently overwrites which user every other open session's next
# request runs as — the exact cause of connections/likes/stats randomly
# showing another account's data or 0. Each session must get its own
# private client so logins can never bleed into each other.

MEDIA_BUCKET = "post-media"
AVATARS_BUCKET = "avatars"
IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".gif", ".webp"}
VIDEO_EXTENSIONS = {".mp4", ".mov", ".avi", ".mkv", ".webm"}

COUNTRIES = [
    "Nigeria", "Ghana", "Cameroon", "Benin Republic", "Togo", "Niger",
    "Chad", "Senegal", "Ivory Coast", "Mali", "Burkina Faso", "Guinea",
    "Sierra Leone", "Liberia", "Gambia", "Kenya", "South Africa",
    "Tanzania", "Uganda", "Rwanda", "Ethiopia", "Egypt", "Morocco",
    "Zambia", "Zimbabwe", "Botswana", "Namibia", "Sudan", "Algeria",
    "Angola", "Mozambique", "Malawi", "United States", "United Kingdom",
    "Canada", "Australia", "Germany", "France", "Italy", "Spain",
    "Netherlands", "Ireland", "Sweden", "Norway", "India", "China",
    "Japan", "Malaysia", "United Arab Emirates", "Saudi Arabia",
    "Qatar", "Turkey", "Brazil", "Other country"
]

DEPARTMENTS = [
    "Computer Science", "Software Engineering", "Information Technology",
    "Cyber Security", "Data Science", "Computer Engineering",
    "Electrical Engineering", "Electronic Engineering",
    "Mechanical Engineering", "Civil Engineering", "Chemical Engineering",
    "Petroleum Engineering", "Mechatronics Engineering",
    "Metallurgical Engineering", "Agricultural Engineering",
    "Medicine & Surgery (MBBS)", "Dentistry", "Pharmacy",
    "Nursing Science", "Medical Laboratory Science", "Physiotherapy",
    "Radiography", "Human Anatomy", "Human Physiology",
    "Public Health", "Veterinary Medicine",
    "Law", "Business Administration", "Accounting", "Banking & Finance",
    "Economics", "Marketing", "Actuarial Science", "Insurance",
    "Public Administration", "Taxation",
    "Mass Communication", "Theatre & Film Studies", "Music",
    "Fine & Applied Arts", "Political Science", "International Relations",
    "Sociology", "Psychology", "Criminology & Security Studies",
    "Social Work", "Philosophy", "Religious Studies", "Linguistics",
    "English Language", "French", "History & International Studies",
    "Library & Information Science", "Guidance & Counselling",
    "Mathematics", "Statistics", "Physics", "Chemistry", "Biochemistry",
    "Microbiology", "Botany", "Zoology", "Biology", "Geology",
    "Geophysics", "Industrial Chemistry",
    "Architecture", "Estate Management", "Urban & Regional Planning",
    "Quantity Surveying", "Building Technology", "Surveying & Geoinformatics",
    "Agriculture", "Agricultural Economics", "Animal Science",
    "Crop Science", "Forestry & Wildlife", "Fisheries",
    "Food Science & Technology",
    "Education", "Educational Management",
    "Yoruba", "Igbo", "Hausa",
    "Other department"
]

# --- FULL NIGERIAN STATE -> LOCAL GOVERNMENT AREA MAPPING (all 36 states + FCT) ---
NIGERIA_LGAS_BY_STATE = {
    "Abia": ["Aba North", "Aba South", "Arochukwu", "Bende", "Ikwuano", "Isiala Ngwa North",
             "Isiala Ngwa South", "Isuikwuato", "Obi Ngwa", "Ohafia", "Osisioma", "Ugwunagbo",
             "Ukwa East", "Ukwa West", "Umuahia North", "Umuahia South", "Umu Nneochi"],
    "Adamawa": ["Demsa", "Fufure", "Ganye", "Girei", "Gombi", "Guyuk", "Hong", "Jada", "Lamurde",
                "Madagali", "Maiha", "Mayo-Belwa", "Michika", "Mubi North", "Mubi South", "Numan",
                "Shelleng", "Song", "Toungo", "Yola North", "Yola South"],
    "Akwa Ibom": ["Abak", "Eastern Obolo", "Eket", "Esit Eket", "Essien Udim", "Etim Ekpo", "Etinan",
                  "Ibeno", "Ibesikpo Asutan", "Ibiono Ibom", "Ika", "Ikono", "Ikot Abasi", "Ikot Ekpene",
                  "Ini", "Itu", "Mbo", "Mkpat Enin", "Nsit Atai", "Nsit Ibom", "Nsit Ubium", "Obot Akara",
                  "Okobo", "Onna", "Oron", "Oruk Anam", "Udung Uko", "Ukanafun", "Uruan",
                  "Urue-Offong/Oruko", "Uyo"],
    "Anambra": ["Aguata", "Anambra East", "Anambra West", "Anaocha", "Awka North", "Awka South",
                "Ayamelum", "Dunukofia", "Ekwusigo", "Idemili North", "Idemili South", "Ihiala",
                "Njikoka", "Nnewi North", "Nnewi South", "Ogbaru", "Onitsha North", "Onitsha South",
                "Orumba North", "Orumba South", "Oyi"],
    "Bauchi": ["Alkaleri", "Bauchi", "Bogoro", "Damban", "Darazo", "Dass", "Gamawa", "Ganjuwa",
               "Giade", "Itas/Gadau", "Jama'are", "Katagum", "Kirfi", "Misau", "Ningi", "Shira",
               "Tafawa Balewa", "Toro", "Warji", "Zaki"],
    "Bayelsa": ["Brass", "Ekeremor", "Kolokuma/Opokuma", "Nembe", "Ogbia", "Sagbama",
                "Southern Ijaw", "Yenagoa"],
    "Benue": ["Ado", "Agatu", "Apa", "Buruku", "Gboko", "Guma", "Gwer East", "Gwer West",
              "Katsina-Ala", "Konshisha", "Kwande", "Logo", "Makurdi", "Obi", "Ogbadibo", "Ohimini",
              "Oju", "Okpokwu", "Otukpo", "Tarka", "Ukum", "Ushongo", "Vandeikya"],
    "Borno": ["Abadam", "Askira/Uba", "Bama", "Bayo", "Biu", "Chibok", "Damboa", "Dikwa", "Gubio",
              "Guzamala", "Gwoza", "Hawul", "Jere", "Kaga", "Kala/Balge", "Konduga", "Kukawa",
              "Kwaya Kusar", "Mafa", "Magumeri", "Maiduguri", "Marte", "Mobbar", "Monguno", "Ngala",
              "Nganzai", "Shani"],
    "Cross River": ["Abi", "Akamkpa", "Akpabuyo", "Bakassi", "Bekwarra", "Biase", "Boki",
                     "Calabar Municipal", "Calabar South", "Etung", "Ikom", "Obanliku", "Obubra",
                     "Obudu", "Odukpani", "Ogoja", "Yakuur", "Yala"],
    "Delta": ["Aniocha North", "Aniocha South", "Bomadi", "Burutu", "Ethiope East", "Ethiope West",
              "Ika North East", "Ika South", "Isoko North", "Isoko South", "Ndokwa East",
              "Ndokwa West", "Okpe", "Oshimili North", "Oshimili South", "Patani", "Sapele", "Udu",
              "Ughelli North", "Ughelli South", "Ukwuani", "Uvwie", "Warri North", "Warri South",
              "Warri South West"],
    "Ebonyi": ["Abakaliki", "Afikpo North", "Afikpo South", "Ebonyi", "Ezza North", "Ezza South",
               "Ikwo", "Ishielu", "Ivo", "Izzi", "Ohaozara", "Ohaukwu", "Onicha"],
    "Edo": ["Akoko-Edo", "Egor", "Esan Central", "Esan North-East", "Esan South-East", "Esan West",
            "Etsako Central", "Etsako East", "Etsako West", "Igueben", "Ikpoba Okha", "Orhionmwon",
            "Oredo", "Ovia North-East", "Ovia South-West", "Owan East", "Owan West", "Uhunmwonde"],
    "Ekiti": ["Ado Ekiti", "Efon", "Ekiti East", "Ekiti South-West", "Ekiti West", "Emure",
              "Gbonyin", "Ido Osi", "Ijero", "Ikere", "Ikole", "Ilejemeje", "Irepodun/Ifelodun",
              "Ise/Orun", "Moba", "Oye"],
    "Enugu": ["Aninri", "Awgu", "Enugu East", "Enugu North", "Enugu South", "Ezeagu", "Igbo Etiti",
              "Igbo Eze North", "Igbo Eze South", "Isi Uzo", "Nkanu East", "Nkanu West", "Nsukka",
              "Oji River", "Udenu", "Udi", "Uzo Uwani"],
    "FCT (Abuja)": ["Abaji", "Abuja Municipal", "Bwari", "Gwagwalada", "Kuje", "Kwali"],
    "Gombe": ["Akko", "Balanga", "Billiri", "Dukku", "Funakaye", "Gombe", "Kaltungo", "Kwami",
              "Nafada", "Shongom", "Yamaltu/Deba"],
    "Imo": ["Aboh Mbaise", "Ahiazu Mbaise", "Ehime Mbano", "Ezinihitte", "Ideato North",
            "Ideato South", "Ihitte/Uboma", "Ikeduru", "Isiala Mbano", "Isu", "Mbaitoli",
            "Ngor Okpala", "Njaba", "Nkwerre", "Nwangele", "Obowo", "Oguta", "Ohaji/Egbema",
            "Okigwe", "Onuimo", "Orlu", "Orsu", "Oru East", "Oru West", "Owerri Municipal",
            "Owerri North", "Owerri West"],
    "Jigawa": ["Auyo", "Babura", "Biriniwa", "Birnin Kudu", "Buji", "Dutse", "Gagarawa", "Garki",
               "Gumel", "Guri", "Gwaram", "Gwiwa", "Hadejia", "Jahun", "Kafin Hausa", "Kaugama",
               "Kazaure", "Kiri Kasama", "Kiyawa", "Maigatari", "Malam Madori", "Miga", "Ringim",
               "Roni", "Sule Tankarkar", "Taura", "Yankwashi"],
    "Kaduna": ["Birnin Gwari", "Chikun", "Giwa", "Igabi", "Ikara", "Jaba", "Jema'a", "Kachia",
               "Kaduna North", "Kaduna South", "Kagarko", "Kajuru", "Kaura", "Kauru", "Kubau",
               "Kudan", "Lere", "Makarfi", "Sabon Gari", "Sanga", "Soba", "Zangon Kataf", "Zaria"],
    "Kano": ["Ajingi", "Albasu", "Bagwai", "Bebeji", "Bichi", "Bunkure", "Dala", "Dambatta",
             "Dawakin Kudu", "Dawakin Tofa", "Doguwa", "Fagge", "Gabasawa", "Garko", "Garun Mallam",
             "Gaya", "Gezawa", "Gwale", "Gwarzo", "Kabo", "Kano Municipal", "Karaye", "Kibiya",
             "Kiru", "Kumbotso", "Kunchi", "Kura", "Madobi", "Makoda", "Minjibir", "Nasarawa",
             "Rano", "Rimin Gado", "Rogo", "Shanono", "Sumaila", "Takai", "Tarauni", "Tofa",
             "Tsanyawa", "Tudun Wada", "Ungogo", "Warawa", "Wudil"],
    "Katsina": ["Bakori", "Batagarawa", "Batsari", "Baure", "Bindawa", "Charanchi", "Dandume",
                "Danja", "Dan Musa", "Daura", "Dutsi", "Dutsin-Ma", "Faskari", "Funtua", "Ingawa",
                "Jibia", "Kafur", "Kaita", "Kankara", "Kankia", "Katsina", "Kurfi", "Kusada",
                "Mai'Adua", "Malumfashi", "Mani", "Mashi", "Matazu", "Musawa", "Rimi", "Sabuwa",
                "Safana", "Sandamu", "Zango"],
    "Kebbi": ["Aleiro", "Arewa Dandi", "Argungu", "Augie", "Bagudo", "Birnin Kebbi", "Bunza",
              "Dandi", "Fakai", "Gwandu", "Jega", "Kalgo", "Koko/Besse", "Maiyama", "Ngaski",
              "Sakaba", "Shanga", "Suru", "Wasagu/Danko", "Yauri", "Zuru"],
    "Kogi": ["Adavi", "Ajaokuta", "Ankpa", "Bassa", "Dekina", "Ibaji", "Idah", "Igalamela Odolu",
             "Ijumu", "Kabba/Bunu", "Kogi", "Lokoja", "Mopa Muro", "Ofu", "Ogori/Magongo", "Okehi",
             "Okene", "Olamaboro", "Omala", "Yagba East", "Yagba West"],
    "Kwara": ["Asa", "Baruten", "Edu", "Ekiti", "Ifelodun", "Ilorin East", "Ilorin South",
              "Ilorin West", "Irepodun", "Isin", "Kaiama", "Moro", "Offa", "Oke Ero", "Oyun",
              "Pategi"],
    "Lagos": ["Agege", "Ajeromi-Ifelodun", "Alimosho", "Amuwo-Odofin", "Apapa", "Badagry", "Epe",
              "Eti Osa", "Ibeju-Lekki", "Ifako-Ijaiye", "Ikeja", "Ikorodu", "Kosofe", "Lagos Island",
              "Lagos Mainland", "Mushin", "Ojo", "Oshodi-Isolo", "Shomolu", "Surulere"],
    "Nasarawa": ["Akwanga", "Awe", "Doma", "Karu", "Keana", "Keffi", "Kokona", "Lafia", "Nasarawa",
                 "Nasarawa Egon", "Obi", "Toto", "Wamba"],
    "Niger": ["Agaie", "Agwara", "Bida", "Borgu", "Bosso", "Chanchaga", "Edati", "Gbako", "Gurara",
              "Katcha", "Kontagora", "Lapai", "Lavun", "Magama", "Mariga", "Mashegu", "Mokwa",
              "Moya", "Paikoro", "Rafi", "Rijau", "Shiroro", "Suleja", "Tafa", "Wushishi"],
    "Ogun": ["Abeokuta North", "Abeokuta South", "Ado-Odo/Ota", "Yewa North", "Yewa South",
             "Ewekoro", "Ifo", "Ijebu East", "Ijebu North", "Ijebu North East", "Ijebu Ode",
             "Ikenne", "Imeko Afon", "Ipokia", "Obafemi Owode", "Odeda", "Odogbolu",
             "Ogun Waterside", "Remo North", "Shagamu"],
    "Ondo": ["Akoko North-East", "Akoko North-West", "Akoko South-West", "Akure North",
             "Akure South", "Ese Odo", "Idanre", "Ifedore", "Ilaje", "Ile Oluji/Okeigbo", "Irele",
             "Odigbo", "Okitipupa", "Ondo East", "Ondo West", "Ose", "Owo"],
    "Osun": ["Aiyedaade", "Aiyedire", "Atakunmosa East", "Atakunmosa West", "Boluwaduro", "Boripe",
             "Ede North", "Ede South", "Egbedore", "Ejigbo", "Ife Central", "Ife East", "Ife North",
             "Ife South", "Ifedayo", "Ifelodun", "Ila", "Ilesa East", "Ilesa West", "Irepodun",
             "Irewole", "Isokan", "Iwo", "Obokun", "Odo Otin", "Ola Oluwa", "Olorunda", "Oriade",
             "Orolu", "Osogbo"],
    "Oyo": ["Afijio", "Akinyele", "Atiba", "Atisbo", "Egbeda", "Ibadan North", "Ibadan North-East",
            "Ibadan North-West", "Ibadan South-East", "Ibadan South-West", "Ibarapa Central",
            "Ibarapa East", "Ibarapa North", "Ido", "Irepo", "Iseyin", "Itesiwaju", "Iwajowa",
            "Kajola", "Lagelu", "Ogbomosho North", "Ogbomosho South", "Ogo Oluwa", "Olorunsogo",
            "Oluyole", "Ona Ara", "Orelope", "Ori Ire", "Oyo East", "Oyo West", "Saki East",
            "Saki West", "Surulere"],
    "Plateau": ["Barkin Ladi", "Bassa", "Bokkos", "Jos East", "Jos North", "Jos South", "Kanam",
                "Kanke", "Langtang North", "Langtang South", "Mangu", "Mikang", "Pankshin",
                "Qua'an Pan", "Riyom", "Shendam", "Wase"],
    "Rivers": ["Abua/Odual", "Ahoada East", "Ahoada West", "Akuku-Toru", "Andoni", "Asari-Toru",
               "Bonny", "Degema", "Eleme", "Emuoha", "Etche", "Gokana", "Ikwerre", "Khana",
               "Obio/Akpor", "Ogba/Egbema/Ndoni", "Ogu/Bolo", "Okrika", "Omuma", "Opobo/Nkoro",
               "Oyigbo", "Port Harcourt", "Tai"],
    "Sokoto": ["Binji", "Bodinga", "Dange Shuni", "Gada", "Goronyo", "Gudu", "Gwadabawa", "Illela",
               "Isa", "Kebbe", "Kware", "Rabah", "Sabon Birni", "Shagari", "Silame", "Sokoto North",
               "Sokoto South", "Tambuwal", "Tangaza", "Tureta", "Wamako", "Wurno", "Yabo"],
    "Taraba": ["Ardo Kola", "Bali", "Donga", "Gashaka", "Gassol", "Ibi", "Jalingo", "Karim Lamido",
               "Kurmi", "Lau", "Sardauna", "Takum", "Ussa", "Wukari", "Yorro", "Zing"],
    "Yobe": ["Bade", "Bursari", "Damaturu", "Fika", "Fune", "Geidam", "Gujba", "Gulani", "Jakusko",
             "Karasuwa", "Machina", "Nangere", "Nguru", "Potiskum", "Tarmuwa", "Yunusari",
             "Yusufari"],
    "Zamfara": ["Anka", "Bakura", "Birnin Magaji/Kiyaw", "Bukkuyum", "Bungudu", "Gummi", "Gusau",
                "Kaura Namoda", "Maradun", "Maru", "Shinkafi", "Talata Mafara", "Tsafe", "Zurmi"],
}
NIGERIAN_STATES = list(NIGERIA_LGAS_BY_STATE.keys())

async def main(page: ft.Page):
    # One private Supabase client per session (per browser tab / user).
    # Created here, inside main(), instead of at module scope, so this
    # session's login token can never overwrite — or be overwritten by —
    # any other concurrently connected user's token. See the note above
    # SUPABASE_URL/SUPABASE_KEY for why a shared client caused random
    # connections/likes/stats data to leak between accounts.
    supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

    page.title = "UniVibe - Master Console"
    page.window_width = 400
    page.window_height = 780
    page.window_resizable = True
    page.scroll = ft.ScrollMode.AUTO
    page.horizontal_alignment = ft.CrossAxisAlignment.CENTER
    page.bgcolor = "#0f172a"

    # ============================================================
    # --- DESIGN SYSTEM ------------------------------------------
    # Single source of truth for color, spacing, and shape. Every new
    # screen or fix should pull from here instead of hand-typing hex
    # codes and magic numbers — that's what let six different border
    # radii (6, 8, 10, 12...) and four different dialog widths creep
    # into the app over time. Nothing below changes what's on screen
    # today; it just gives the existing palette real names so the next
    # change converges toward one visual language instead of drifting
    # further apart.
    # ============================================================
    COLOR_BG        = "#0f172a"  # page background + "inset" surfaces nested inside a card
    COLOR_CARD      = "#1e293b"  # cards, dialogs, the bottom nav bar
    COLOR_BORDER    = "#334155"  # dividers, input outlines, subtle separators
    COLOR_PRIMARY   = "#6366f1"  # brand indigo — primary actions, active nav, links
    COLOR_SUCCESS   = "#10b981"  # confirmations, "accept", positive status text
    COLOR_DANGER    = "#f43f5e"  # destructive actions, errors, unread-alert red
    COLOR_WARNING   = "#eab308"  # pending states, anonymous/secret content accents
    COLOR_TEXT_MUTED = "#94a3b8"  # secondary text, placeholders, inactive nav
    COLOR_TEXT_FAINT = "#64748b"  # tertiary text, disabled icons, timestamps
    COLOR_TEXT_BODY  = "#e2e8f0"  # primary body copy on dark surfaces (post text, bios, bubbles)

    COLOR_UNREAD   = "#27314a"  # unread notification row highlight
    COLOR_WHISPER  = "#271c24"  # Whisper Wall's anonymous-post accent surface
    COLOR_WHATSAPP = "#25D366"  # WhatsApp brand green, for the "share via WhatsApp" button only

    SPACE_XS = 4   # tight gaps: icon-to-label, chip padding
    SPACE_SM = 6   # compact rows, action bars
    SPACE_MD = 10  # standard card padding, list-item spacing
    SPACE_LG = 16  # section spacing, generous card padding

    RADIUS_SM = 8    # inset elements sitting inside a card (e.g. comment bubbles)
    RADIUS_MD = 12   # standard cards: posts, friend rows, notifications, list items
    RADIUS_LG = 16   # chat bubbles and other rounder, "pill-like" surfaces
    DIALOG_WIDTH = 300  # every AlertDialog content column standardizes on this



    # --- DATABASE FETCHING FUNCTION ---
    def get_posts():
        try:
            response = supabase.table("posts").select("*").order("created_at", desc=True).limit(50).execute()
            return response.data
        except Exception as e:
            print(f"Error fetching posts: {e}")
            return []

    def get_likes_map(post_ids):
        """Returns {post_id: {like_count, user_liked}} for a list of post IDs."""
        if not post_ids:
            return {}
        try:
            resp = supabase.rpc("get_post_likes", {
                "p_post_ids": post_ids,
                "p_user_id": get_cached_user_id() or "00000000-0000-0000-0000-000000000000"
            }).execute()
            return {r["post_id"]: r for r in (resp.data or [])}
        except Exception as e:
            print(f"Likes fetch error: {e}")
            return {}

    def handle_toggle_like(post_id, like_btn, like_count_text, post_owner_id):
        try:
            resp = supabase.rpc("toggle_post_like", {
                "p_post_id": post_id,
                "p_user_id": get_cached_user_id()
            }).execute()
            new_count = resp.data or 0
            like_count_text.value = str(new_count)
            # Toggle heart colour
            current_color = like_btn.icon_color
            now_liked = current_color != COLOR_DANGER
            like_btn.icon_color = COLOR_DANGER if now_liked else COLOR_TEXT_FAINT
            page.update()
            if now_liked:
                create_notification(post_owner_id, "like",
                                    f"{user_cache.get('username','Someone')} liked your post", post_id)
        except Exception as ex:
            print(f"Like error: {ex}")

    def open_comments_dialog(post_id, post_username, post_owner_id=None):
        comment_input = ft.TextField(
            hint_text="Write a comment…", expand=True, dense=True, color="white",
            border_color=COLOR_BORDER, content_padding=10
        )
        comments_col = ft.Column(spacing=6, scroll=ft.ScrollMode.ALWAYS, height=220, width=300)
        status = ft.Text("", size=11)
        send_btn = ft.IconButton(icon=ft.Icons.SEND_ROUNDED, icon_color=COLOR_PRIMARY)

        def load_comments():
            comments_col.controls.clear()
            try:
                resp = supabase.rpc("get_post_comments", {"p_post_id": post_id}).execute()
                for c in (resp.data or []):
                    comments_col.controls.append(
                        ft.Container(
                            content=ft.Column([
                                ft.Text(c["username"], weight=ft.FontWeight.BOLD,
                                        color=COLOR_PRIMARY, size=12),
                                ft.Text(c["content"], color=COLOR_TEXT_BODY, size=13)
                            ], spacing=2),
                            padding=SPACE_MD, bgcolor=COLOR_BG, border_radius=RADIUS_SM
                        )
                    )
                if not resp.data:
                    comments_col.controls.append(
                        ft.Text("No comments yet. Be first!", color=COLOR_TEXT_MUTED, size=12)
                    )
            except Exception as ex:
                print(f"Comments load error: {ex}")
                comments_col.controls.append(
                    ft.Text("Couldn't load comments — try closing and reopening.", color=COLOR_DANGER, size=12)
                )
            page.update()

        def submit_comment(e):
            content = (comment_input.value or "").strip()
            if not content:
                status.value = "Write something first."
                status.color = COLOR_TEXT_MUTED
                page.update()
                return
            send_btn.disabled = True
            status.value = ""
            page.update()
            try:
                supabase.rpc("add_post_comment", {
                    "p_post_id": post_id,
                    "p_user_id": get_cached_user_id(),
                    "p_username": user_cache.get("username", "Unknown"),
                    "p_content": content
                }).execute()
                comment_input.value = ""
                send_btn.disabled = False
                load_comments()  # already calls page.update()
                create_notification(post_owner_id, "comment",
                                    f"{user_cache.get('username','Someone')} commented on your post", post_id)
            except Exception as ex:
                send_btn.disabled = False
                status.value = f"Couldn't post comment: {str(ex)}"
                status.color = COLOR_DANGER
                page.update()

        send_btn.on_click = submit_comment

        dlg = ft.AlertDialog(
            title=ft.Text(f"Comments on {post_username}'s post", color="white", size=14),
            bgcolor=COLOR_CARD,
            content=ft.Container(
                content=ft.Column([
                    comments_col,
                    ft.Divider(height=8, color=COLOR_BORDER),
                    ft.Row([comment_input, send_btn], spacing=4,
                           vertical_alignment=ft.CrossAxisAlignment.CENTER),
                    status
                ], spacing=8, tight=True),
                width=DIALOG_WIDTH
            ),
            actions=[ft.TextButton("Close", on_click=lambda e: close_dlg(dlg))]
        )

        def close_dlg(d):
            d.open = False
            page.update()

        page.overlay.append(dlg)
        dlg.open = True
        load_comments()
        page.update()

    def open_share_dialog(post):
        share_username_input = ft.TextField(hint_text="Friend's username", width=220, dense=True, color="white")
        share_status = ft.Text("", size=11)

        def share_to_chat(e):
            target = (share_username_input.value or "").strip()
            if not target:
                share_status.value = "Enter a username first."
                share_status.color = COLOR_DANGER
                page.update()
                return
            conv_id, error = get_or_create_conversation(target)
            if error:
                share_status.value = error
                share_status.color = COLOR_DANGER
                page.update()
                return
            preview = (post.get("content") or "")[:100]
            msg = f"\U0001F4E4 Shared a post: {preview}"
            if post.get("media_url"):
                msg += f"\n{post['media_url']}"
            sent_ok, send_err = send_message(conv_id, msg)
            if not sent_ok:
                share_status.value = send_err or "Couldn't share — try again."
                share_status.color = COLOR_DANGER
                page.update()
                return
            share_status.value = "Shared! ✅"
            share_status.color = COLOR_SUCCESS
            share_username_input.value = ""
            page.update()

        def share_whatsapp(e):
            text = f"Check this out on UniVibe: {post.get('content') or ''}"
            if post.get("media_url"):
                text += f" {post['media_url']}"
            encoded = urllib.parse.quote(text)
            page.launch_url(f"https://wa.me/?text={encoded}")

        def close_dlg(d):
            d.open = False
            page.update()

        dlg = ft.AlertDialog(
            title=ft.Text("Share Post", color="white", size=14),
            bgcolor=COLOR_CARD,
            content=ft.Column([
                ft.Text("Share to a friend's chat:", color=COLOR_TEXT_MUTED, size=12),
                ft.Row([share_username_input,
                        ft.IconButton(icon=ft.Icons.SEND_ROUNDED, icon_color=COLOR_PRIMARY, on_click=share_to_chat)]),
                share_status,
                ft.Divider(color=COLOR_BORDER),
                ft.ElevatedButton(
                    content=ft.Row([ft.Icon(ft.Icons.SHARE_ROUNDED, color="white", size=16),
                                    ft.Text("Share via WhatsApp", color="white")], spacing=6),
                    bgcolor=COLOR_WHATSAPP, on_click=share_whatsapp
                )
            ], tight=True, spacing=10, width=DIALOG_WIDTH),
            actions=[ft.TextButton("Close", on_click=lambda e: close_dlg(dlg))]
        )
        page.overlay.append(dlg)
        dlg.open = True
        page.update()

    def handle_repost(post):
        user_id = get_cached_user_id()
        username = user_cache.get("username", "Unknown")
        if not user_id:
            return
        try:
            is_anon_original = post.get("is_anonymous", False)
            source_label = "an anonymous secret" if is_anon_original else f"@{post.get('username', 'Unknown')}"
            prefix = f"\U0001F501 Repost from {source_label}: "
            supabase.table("posts").insert({
                "user_id": user_id,
                "username": username,
                "content": prefix + (post.get("content") or ""),
                "media_url": post.get("media_url"),
                "media_type": post.get("media_type"),
                "is_anonymous": False
            }).execute()
            render_public_feed()
        except Exception as ex:
            print(f"Repost error: {ex}")

    def extract_storage_path(url, bucket):
        """Pulls the storage path out of a Supabase public URL, e.g.
        '.../storage/v1/object/public/post-media/abc/xyz.jpg' -> 'abc/xyz.jpg'"""
        if not url:
            return None
        marker = f"/public/{bucket}/"
        if marker in url:
            return url.split(marker, 1)[1]
        return None

    def cleanup_post_media(deleted_post):
        """Removes the post's media file from storage — but only if no other
        post (e.g. a repost, which reuses the same file URL) still needs it."""
        media_url = deleted_post.get("media_url")
        if not media_url:
            return
        try:
            others = supabase.table("posts").select("id").eq("media_url", media_url).neq("id", deleted_post["id"]).execute()
            if others.data:
                return  # still referenced by another post (e.g. a repost) — keep the file
            storage_path = extract_storage_path(media_url, MEDIA_BUCKET)
            if storage_path:
                supabase.storage.from_(MEDIA_BUCKET).remove([storage_path])
        except Exception as ex:
            print(f"Media cleanup error: {ex}")

    def handle_delete_post(post):
        user_id = get_cached_user_id()
        if not user_id:
            return
        try:
            cleanup_post_media(post)
            supabase.rpc("delete_own_post", {
                "p_post_id": post["id"],
                "p_user_id": user_id
            }).execute()
            render_public_feed()
        except Exception as ex:
            print(f"Delete post error: {ex}")

    REPORT_REASONS = ["Harassment or bullying", "Hate speech", "Nudity or sexual content",
                       "Spam", "False information", "Other"]

    def open_report_post_dialog(post_id):
        reason_dd = ft.Dropdown(
            label="Reason", width=DIALOG_WIDTH, color="white",
            options=[ft.dropdown.Option(r) for r in REPORT_REASONS]
        )
        status = ft.Text("", size=11)

        def close_dlg(d):
            d.open = False
            page.update()

        def submit_report(e):
            if not reason_dd.value:
                status.value = "Please choose a reason."
                status.color = COLOR_DANGER
                page.update()
                return
            if report_post_action(post_id, reason_dd.value):
                status.value = "Reported. Our team will review it."
                status.color = COLOR_SUCCESS
                page.update()
            else:
                status.value = "Couldn't submit report — try again."
                status.color = COLOR_DANGER
                page.update()

        dlg = ft.AlertDialog(
            title=ft.Text("Report Post", color="white", size=16),
            bgcolor=COLOR_CARD,
            content=ft.Column([reason_dd, status], tight=True, spacing=10),
            actions=[
                ft.TextButton("Submit", on_click=submit_report),
                ft.TextButton("Close", on_click=lambda ev: close_dlg(dlg))
            ]
        )
        page.overlay.append(dlg)
        dlg.open = True
        page.update()



    def get_real_users(search_query=""):
        """Fetch registered users, filtered and capped at the database level —
        never pulls the whole profiles table, scales regardless of user count."""
        try:
            current_id = get_cached_user_id()
            blocked = list(get_blocked_ids())
            # Strip characters that would break Supabase's or_() filter syntax
            q = (search_query or "").strip().replace(",", "").replace("%", "")

            query = supabase.table("profiles").select("user_id, username, country, state, department, avatar_url")

            if q:
                query = query.ilike("username", f"%{q}%")

            if current_id:
                query = query.neq("user_id", current_id)

            if blocked:
                query = query.not_.in_("user_id", blocked)

            resp = query.order("username").limit(50).execute()
            return resp.data or []
        except Exception as e:
            print(f"Error fetching users: {e}")
            return []

    def get_whisper_posts():
        try:
            response = supabase.table("posts").select("*").eq("is_anonymous", True).order("created_at", desc=True).limit(50).execute()
            return response.data
        except Exception as e:
            print(f"Error fetching whisper posts: {e}")
            return []

    # --- FEED STORAGE CONTAINERS ---
    public_feed_layout = ft.Column(spacing=10)
    friends_layout = ft.Column(spacing=8, scroll=ft.ScrollMode.ALWAYS, height=400)
    whisper_feed_layout = ft.Column(spacing=10)

    # ============================================================
    # --- INLINE VIDEO PLAYBACK ----------------------------------
    # One shared player-builder used by every tap-to-play surface (Feed
    # cards, Reels, the immersive post viewer) so a tap always swaps the
    # placeholder for a real, controllable video instance streaming the
    # Supabase public URL directly — never a redirect out to the system
    # browser, and never a dead tap target left behind after playback
    # starts.
    # ============================================================
    def build_inline_video_player(url, width, height, autoplay=True):
        """Returns a control that plays `url` in place. Uses the flet_video
        package's Video control (imported as `ftv` at the top of the file)
        when it's installed; if it isn't, fails over to a clearly-labeled,
        actually-tappable control that opens the stream externally instead
        of leaving a silently broken placeholder on screen."""
        if not url or ftv is None:
            return ft.Container(
                content=ft.Column([
                    ft.Icon(ft.Icons.OPEN_IN_NEW_ROUNDED, color="white", size=32),
                    ft.Text(
                        "Video player not installed.\nTap to open in browser instead."
                        if ftv is None else "No video to play.",
                        color="white", size=12, text_align=ft.TextAlign.CENTER
                    )
                ], alignment=ft.MainAxisAlignment.CENTER, horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                   spacing=6),
                width=width, height=height, bgcolor=COLOR_CARD, border_radius=RADIUS_MD,
                alignment=ft.Alignment.CENTER,
                on_click=(lambda e: page.launch_url(url)) if url else None
            )
        return ftv.Video(
            playlist=[ftv.VideoMedia(resource=url)],
            width=width,
            height=height,
            autoplay=autoplay,
            show_controls=True,
        )

    def make_play_video_handler(container, url, width, height):
        """Swaps a placeholder Container's content for a live player on
        tap, then disables the placeholder's own on_click (the player
        supplies its own controls from here on) — a clean one-way state
        transition from 'preview' to 'playing', no leftover dead tap
        target underneath the player."""
        def handler(e):
            if not url:
                return
            container.content = build_inline_video_player(url, width, height)
            container.padding = 0
            container.on_click = None
            page.update()
        return handler

    # --- RENDERING FUNCS ---
    def render_public_feed():
        public_feed_layout.controls.clear()
        blocked = get_blocked_ids()
        posts = [p for p in get_posts() if p.get("user_id") not in blocked]
        post_ids = [p["id"] for p in posts if p.get("id")]
        likes_map = get_likes_map(post_ids)

        for p in posts:
            is_anon = p.get("is_anonymous", False)
            display_name = "Anonymous Ghost \U0001F47B" if is_anon else p.get("username", "Unknown")
            name_color = COLOR_DANGER if is_anon else COLOR_PRIMARY
            name_icon = ft.Icons.SECURITY_ROUNDED if is_anon else ft.Icons.ACCOUNT_CIRCLE_ROUNDED
            icon_color = COLOR_DANGER if is_anon else COLOR_PRIMARY

            def make_name_tap(uname=p.get("username")):
                def on_tap(e):
                    if uname:
                        load_other_profile(uname)
                return on_tap

            if not is_anon:
                name_widget = ft.GestureDetector(
                    content=ft.Text(display_name, weight=ft.FontWeight.BOLD, color=name_color),
                    on_tap=make_name_tap()
                )
            else:
                name_widget = ft.Text(display_name, weight=ft.FontWeight.BOLD, color=name_color)

            post_body = [
                ft.Row([ft.Icon(name_icon, color=icon_color, size=18), name_widget])
            ]
            if p.get("content"):
                post_body.append(ft.Text(p["content"], color=COLOR_TEXT_BODY, size=14))

            media_url = p.get("media_url")
            if media_url and p.get("media_type") == "image":
                post_body.append(
                    ft.Image(src=media_url, width=300, height=180, fit=ft.BoxFit.COVER, border_radius=RADIUS_MD)
                )
            elif media_url and p.get("media_type") == "video":
                feed_video_container = ft.Container(
                    content=ft.Row([ft.Icon(ft.Icons.PLAY_CIRCLE_ROUNDED, color="white"),
                                    ft.Text("Video attached — tap to play", color="white", size=12)]),
                    padding=SPACE_MD, bgcolor=COLOR_BORDER, border_radius=RADIUS_SM,
                )
                feed_video_container.on_click = make_play_video_handler(
                    feed_video_container, media_url, 300, 180
                )
                post_body.append(feed_video_container)

            # Like / Comment action bar
            post_id = p.get("id")
            like_info = likes_map.get(post_id, {})
            like_count = like_info.get("like_count", 0)
            user_liked = like_info.get("user_liked", False)
            like_icon_color = COLOR_DANGER if user_liked else COLOR_TEXT_FAINT

            like_count_text = ft.Text(str(like_count), color=COLOR_TEXT_MUTED, size=12)
            like_btn = ft.IconButton(
                icon=ft.Icons.FAVORITE_ROUNDED,
                icon_color=like_icon_color,
                icon_size=18
            )
            # Wire after creation so we can pass references
            def make_like_handler(pid=post_id, lb=like_btn, lct=like_count_text, owner=p.get("user_id")):
                like_btn.on_click = lambda e: handle_toggle_like(pid, lb, lct, owner)
            make_like_handler()

            comment_btn = ft.IconButton(
                icon=ft.Icons.CHAT_BUBBLE_OUTLINE_ROUNDED,
                icon_color=COLOR_TEXT_FAINT, icon_size=18,
                on_click=lambda e, pid=post_id, uname=p.get("username","Unknown"), owner=p.get("user_id"): open_comments_dialog(pid, uname, owner)
            )

            share_btn = ft.IconButton(
                icon=ft.Icons.SHARE_ROUNDED,
                icon_color=COLOR_TEXT_FAINT, icon_size=18,
                tooltip="Share",
                on_click=lambda e, post=p: open_share_dialog(post)
            )

            repost_btn = ft.IconButton(
                icon=ft.Icons.REPEAT_ROUNDED,
                icon_color=COLOR_TEXT_FAINT, icon_size=18,
                tooltip="Repost",
                on_click=lambda e, post=p: handle_repost(post)
            )

            action_row_controls = [like_btn, like_count_text, comment_btn, share_btn, repost_btn]

            if p.get("user_id") == get_cached_user_id():
                delete_btn = ft.IconButton(
                    icon=ft.Icons.DELETE_OUTLINE_ROUNDED,
                    icon_color=COLOR_TEXT_FAINT, icon_size=18,
                    tooltip="Delete post",
                    on_click=lambda e, post=p: handle_delete_post(post)
                )
                action_row_controls.append(delete_btn)
            else:
                report_btn = ft.IconButton(
                    icon=ft.Icons.FLAG_ROUNDED,
                    icon_color=COLOR_TEXT_FAINT, icon_size=18,
                    tooltip="Report post",
                    on_click=lambda e, pid=post_id: open_report_post_dialog(pid)
                )
                action_row_controls.append(report_btn)

            post_body.append(ft.Row(action_row_controls, spacing=0))

            public_feed_layout.controls.append(
                ft.Container(
                    content=ft.Column(post_body, spacing=6),
                    padding=SPACE_LG, bgcolor=COLOR_CARD, border_radius=RADIUS_MD, width=340
                )
            )
        page.update()

    def render_friends_section(search_query=""):
        friends_layout.controls.clear()
        users = get_real_users(search_query)
        connections_map = get_my_connections_map()
        if not users:
            friends_layout.controls.append(
                ft.Text("No students found. Try a different search!", color=COLOR_TEXT_MUTED, size=12)
            )
        for u in users:
            uname = u.get("username", "Unknown")
            target_id = u.get("user_id")
            detail_parts = [x for x in [u.get("department"), u.get("country")] if x]
            detail_text = " · ".join(detail_parts) if detail_parts else "No details yet"
            conn_info = connections_map.get(target_id)

            def view_this(e, name=uname):
                load_other_profile(name)

            def chat_this(e, name=uname):
                conv_id, error = get_or_create_conversation(name)
                if not error:
                    set_panel_visibility(chats=True)
                    open_thread(conv_id, name)

            # Decide the + button's icon/color/behavior for this row from the
            # bulk connections lookup — no per-row network call needed.
            if conn_info and conn_info["status"] == "accepted":
                add_icon, add_color, add_tip, add_disabled = ft.Icons.CHECK_CIRCLE_ROUNDED, COLOR_TEXT_FAINT, "Connected", True
            elif conn_info and conn_info["status"] == "pending" and conn_info["is_requester"]:
                add_icon, add_color, add_tip, add_disabled = ft.Icons.HOURGLASS_TOP_ROUNDED, COLOR_TEXT_FAINT, "Pending", True
            elif conn_info and conn_info["status"] == "pending" and not conn_info["is_requester"]:
                add_icon, add_color, add_tip, add_disabled = ft.Icons.PERSON_ADD_ALT_1_ROUNDED, COLOR_WARNING, "Respond to request", False
            else:
                add_icon, add_color, add_tip, add_disabled = ft.Icons.PERSON_ADD_ALT_1_ROUNDED, COLOR_PRIMARY, "Add friend", False

            def make_add_click(target_id=target_id, uname=uname, info=conn_info):
                def handler(e):
                    if info and info["status"] == "pending" and not info["is_requester"]:
                        def handle_result(accept, error):
                            render_friends_section(search_input.value)
                            render_pending_requests_banner()
                        open_respond_dialog(info["request_id"], uname, on_responded=handle_result)
                        return
                    if info and (info["status"] == "accepted" or (info["status"] == "pending" and info["is_requester"])):
                        return  # already handled — button is disabled in these states
                    send_connection_request(target_id)
                    render_friends_section(search_input.value)
                return handler

            friends_layout.controls.append(
                ft.Container(
                    content=ft.Row([
                        ft.Column([
                            ft.Text(uname, color="white", weight="bold", size=13),
                            ft.Text(detail_text, color=COLOR_TEXT_MUTED, size=11)
                        ], spacing=2, expand=True),
                        ft.Row([
                            ft.IconButton(icon=add_icon, icon_color=add_color, tooltip=add_tip,
                                          disabled=add_disabled, on_click=make_add_click(), icon_size=20),
                            ft.IconButton(icon=ft.Icons.PERSON_ROUNDED, icon_color=COLOR_PRIMARY,
                                          tooltip="View profile", on_click=view_this),
                            ft.IconButton(icon=ft.Icons.CHAT_BUBBLE_OUTLINE_ROUNDED, icon_color=COLOR_SUCCESS,
                                          tooltip="Message", on_click=chat_this),
                        ], spacing=0)
                    ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                    padding=SPACE_MD, bgcolor=COLOR_CARD, border_radius=RADIUS_MD, width=340
                )
            )
        page.update()

    def render_whisper_feed(reveal_names=False):
        whisper_feed_layout.controls.clear()
        blocked = get_blocked_ids()
        posts = [w for w in get_whisper_posts() if w.get("user_id") not in blocked]
        if not posts:
            whisper_feed_layout.controls.append(
                ft.Text("No secrets yet. Be the first to share one!", color=COLOR_TEXT_MUTED, size=12)
            )
        for w in posts:
            real_name = w.get("username", "Unknown")
            display_tag = f"Anonymous Ghost [Real: {real_name}]" if reveal_names else "Anonymous Ghost \U0001F47B"
            header_color = COLOR_WARNING if reveal_names else COLOR_DANGER
            whisper_feed_layout.controls.append(
                ft.Container(
                    content=ft.Column([
                        ft.Row([ft.Icon(ft.Icons.SECURITY_ROUNDED, color=header_color), ft.Text(display_tag, weight=ft.FontWeight.BOLD, color=header_color)]),
                        ft.Text(w.get("content", ""), color=COLOR_TEXT_BODY)
                    ]), padding=SPACE_LG, bgcolor=COLOR_WHISPER, border_radius=RADIUS_MD, width=340
                )
            )
        page.update()

    def handle_post_whisper(e):
        content = (whisper_text_box.value or "").strip()
        if not content:
            whisper_status_text.value = "Write a secret first!"
            whisper_status_text.color = COLOR_DANGER
            page.update()
            return
        try:
            real_username = user_cache.get("username", "Unknown")
            user_id = get_cached_user_id()
            supabase.table("posts").insert({
                "user_id": user_id,
                "username": real_username,
                "content": content,
                "media_url": None,
                "media_type": None,
                "is_anonymous": True
            }).execute()
            whisper_text_box.value = ""
            whisper_status_text.value = "Secret posted! 🤫"
            whisper_status_text.color = COLOR_SUCCESS
            page.update()
            render_whisper_feed(reveal_names=creator_admin_switch.value)
        except Exception as ex:
            whisper_status_text.value = f"Failed to post: {str(ex)}"
            whisper_status_text.color = COLOR_DANGER
            page.update()

    # --- TAB: REELS (short video feed) ---
    reels_layout = ft.Column(spacing=12, scroll=ft.ScrollMode.AUTO, expand=True)

    def render_reels_feed():
        reels_layout.controls.clear()
        blocked = get_blocked_ids()
        posts = [p for p in get_posts() if p.get("user_id") not in blocked]
        video_posts = [p for p in posts if p.get("media_type") == "video" and p.get("media_url")]
        if not video_posts:
            reels_layout.controls.append(
                ft.Container(
                    content=ft.Text("No reels yet. Post a video from Feed to start!",
                                    color=COLOR_TEXT_MUTED, size=13),
                    padding=20, alignment=ft.Alignment.CENTER
                )
            )
        for p in video_posts:
            is_anon = p.get("is_anonymous", False)
            display_name = "Anonymous Ghost \U0001F47B" if is_anon else p.get("username", "Unknown")

            reel_video_container = ft.Container(
                content=ft.Column([
                    ft.Icon(ft.Icons.PLAY_CIRCLE_ROUNDED, color="white", size=48),
                    ft.Text("Tap to play", color="white", size=12)
                ], alignment=ft.MainAxisAlignment.CENTER,
                   horizontal_alignment=ft.CrossAxisAlignment.CENTER),
                width=340, height=420, bgcolor=COLOR_CARD, border_radius=RADIUS_MD,
                alignment=ft.Alignment.CENTER,
            )
            reel_video_container.on_click = make_play_video_handler(
                reel_video_container, p["media_url"], 340, 420
            )

            reels_layout.controls.append(
                ft.Container(
                    content=ft.Column([
                        reel_video_container,
                        ft.Row([
                            ft.Icon(ft.Icons.SECURITY_ROUNDED if is_anon else ft.Icons.ACCOUNT_CIRCLE_ROUNDED,
                                    color=COLOR_DANGER if is_anon else COLOR_PRIMARY, size=16),
                            ft.Text(display_name, weight=ft.FontWeight.BOLD,
                                    color=COLOR_DANGER if is_anon else COLOR_PRIMARY, size=13)
                        ]),
                        ft.Text(p.get("content") or "", color=COLOR_TEXT_BODY, size=12)
                    ], spacing=6),
                    padding=8
                )
            )
        page.update()

    panel_reels = ft.Column([
        ft.Text("Reels \U0001F3AC", size=18, weight=ft.FontWeight.BOLD, color="white"),
        reels_layout
    ], visible=False, horizontal_alignment=ft.CrossAxisAlignment.CENTER)

    # --- TAB: NOTIFICATIONS ---
    notifications_layout = ft.Column(spacing=8)

    NOTIF_ICONS = {
        "like": (ft.Icons.FAVORITE_ROUNDED, COLOR_DANGER),
        "comment": (ft.Icons.CHAT_BUBBLE_ROUNDED, COLOR_PRIMARY),
        "message": (ft.Icons.MAIL, COLOR_SUCCESS),
        "friend_request": (ft.Icons.PERSON_ADD_ALT_1_ROUNDED, COLOR_WARNING),
        "friend_accept": (ft.Icons.CHECK_CIRCLE_ROUNDED, COLOR_SUCCESS),
    }

    def render_notifications_panel():
        notifications_layout.controls.clear()
        user_id = get_cached_user_id()
        if not user_id:
            return
        try:
            resp = supabase.rpc("get_notifications", {"p_user_id": user_id}).execute()
            notifs = resp.data or []
        except Exception as ex:
            print(f"Notifications load error: {ex}")
            notifs = []

        if not notifs:
            notifications_layout.controls.append(
                ft.Text("No notifications yet.", color=COLOR_TEXT_MUTED, size=13)
            )
        for n in notifs:
            icon, color = NOTIF_ICONS.get(n.get("type"), (ft.Icons.NOTIFICATIONS, COLOR_TEXT_MUTED))
            is_unread = not n.get("is_read", True)
            notifications_layout.controls.append(
                ft.Container(
                    content=ft.Row([
                        ft.Icon(icon, color=color, size=20),
                        ft.Text(n.get("message", ""), color="white" if is_unread else COLOR_TEXT_MUTED, size=13, expand=True)
                    ], spacing=10),
                    padding=SPACE_LG,
                    bgcolor=COLOR_UNREAD if is_unread else COLOR_CARD,
                    border_radius=RADIUS_MD, width=340
                )
            )
        page.update()

    def refresh_notification_badge():
        user_id = get_cached_user_id()
        if not user_id:
            return
        try:
            resp = supabase.rpc("get_unread_notification_count", {"p_user_id": user_id}).execute()
            count = resp.data or 0
            if count and count > 0:
                nav_buttons["notifications"].icon = ft.Icons.NOTIFICATIONS_ACTIVE_ROUNDED
                nav_buttons["notifications"].icon_color = COLOR_DANGER
            else:
                nav_buttons["notifications"].icon = ft.Icons.NOTIFICATIONS_NONE_ROUNDED
                if active_nav_key["value"] != "notifications":
                    nav_buttons["notifications"].icon_color = NAV_INACTIVE
            page.update()
        except Exception as ex:
            print(f"Badge refresh error: {ex}")

    panel_notifications = ft.Column([
        ft.Text("Notifications \U0001F514", size=18, weight=ft.FontWeight.BOLD, color="white"),
        notifications_layout
    ], visible=False, horizontal_alignment=ft.CrossAxisAlignment.CENTER)

    # --- CUSTOM NAVIGATION ACTIONS ---
    NAV_ACTIVE = COLOR_PRIMARY
    NAV_INACTIVE = COLOR_TEXT_MUTED
    active_nav_key = {"value": "feed"}

    def highlight_nav(active_key):
        active_nav_key["value"] = active_key
        for key, btn in nav_buttons.items():
            if key == "notifications" and btn.icon == ft.Icons.NOTIFICATIONS_ACTIVE_ROUNDED:
                continue  # keep the red "unread" color even if this tab isn't active
            btn.icon_color = NAV_ACTIVE if key == active_key else NAV_INACTIVE
        page.update()

    def nav_to_feed(e):
        set_panel_visibility(feed=True)
        render_public_feed()
        highlight_nav("feed")

    def nav_to_secrets(e):
        set_panel_visibility(secrets=True)
        render_whisper_feed(reveal_names=creator_admin_switch.value)
        highlight_nav("secrets")

    def nav_to_chats(e):
        chat_state["polling_active"] = False
        panel_chats_thread.visible = False
        panel_chats_inbox.visible = True
        set_panel_visibility(chats=True)
        render_conversations_list(force=True)
        chat_state["inbox_polling_active"] = True
        page.run_task(poll_inbox_loop)
        highlight_nav("chats")

    def nav_to_people(e):
        set_panel_visibility(people=True)
        render_friends_section()
        render_pending_requests_banner()
        highlight_nav("people")

    def nav_to_reels(e):
        set_panel_visibility(reels=True)
        render_reels_feed()
        highlight_nav("reels")

    def nav_to_notifications(e):
        set_panel_visibility(notifications=True)
        render_notifications_panel()
        highlight_nav("notifications")
        nav_buttons["notifications"].icon = ft.Icons.NOTIFICATIONS_NONE_ROUNDED
        nav_buttons["notifications"].icon_color = NAV_ACTIVE
        page.update()
        user_id = get_cached_user_id()
        if user_id:
            try:
                supabase.rpc("mark_notifications_read", {"p_user_id": user_id}).execute()
            except Exception as ex:
                print(f"Mark read error: {ex}")

    def nav_to_profile(e):
        set_panel_visibility(profile=True)
        load_own_profile()
        highlight_nav("profile")

    def close_menu_dialog(d):
        d.open = False
        page.update()

    def open_settings_from_menu(dlg):
        close_menu_dialog(dlg)
        open_account_settings(None)

    def open_profile_from_menu(dlg):
        close_menu_dialog(dlg)
        nav_to_profile(None)

    def handle_logout_from_menu(dlg):
        close_menu_dialog(dlg)
        page.run_task(handle_logout, None)

    def open_blocked_users_dialog(menu_dlg=None):
        if menu_dlg:
            close_menu_dialog(menu_dlg)

        blocked_list_col = ft.Column(spacing=8, scroll=ft.ScrollMode.AUTO, height=280, width=DIALOG_WIDTH)

        def load_blocked_list():
            blocked_list_col.controls.clear()
            user_id = get_cached_user_id()
            ids = list(get_blocked_ids(force_refresh=True))
            if not ids:
                blocked_list_col.controls.append(
                    ft.Text("You haven't blocked anyone.", color=COLOR_TEXT_MUTED, size=12)
                )
                page.update()
                return
            try:
                resp = supabase.table("profiles").select("user_id, username").in_("user_id", ids).execute()
                for u in (resp.data or []):
                    def make_unblock(target=u.get("user_id"), uname=u.get("username", "Unknown")):
                        def do_unblock(e):
                            unblock_user_action(target)
                            load_blocked_list()
                        return do_unblock
                    blocked_list_col.controls.append(
                        ft.Row([
                            ft.Text(f"@{u.get('username', 'Unknown')}", color="white", size=13, expand=True),
                            ft.TextButton("Unblock", on_click=make_unblock())
                        ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN)
                    )
            except Exception as ex:
                print(f"Load blocked list error: {ex}")
            page.update()

        def close_dlg(d):
            d.open = False
            page.update()

        dlg = ft.AlertDialog(
            title=ft.Text("Blocked Users", color="white", size=16),
            bgcolor=COLOR_CARD,
            content=blocked_list_col,
            actions=[ft.TextButton("Close", on_click=lambda ev: close_dlg(dlg))]
        )
        page.overlay.append(dlg)
        dlg.open = True
        load_blocked_list()
        page.update()

    def open_main_menu(e):
        dlg = ft.AlertDialog(
            title=ft.Text("Menu", color="white", size=16),
            bgcolor=COLOR_CARD,
            content=ft.Column([
                ft.ListTile(
                    leading=ft.Icon(ft.Icons.PERSON_ROUNDED, color=COLOR_PRIMARY),
                    title=ft.Text("Profile", color="white"),
                    subtitle=ft.Text("Edit your bio, avatar & school", color=COLOR_TEXT_MUTED, size=11),
                    on_click=lambda ev: open_profile_from_menu(dlg)
                ),
                ft.ListTile(
                    leading=ft.Icon(ft.Icons.SETTINGS_ROUNDED, color=COLOR_PRIMARY),
                    title=ft.Text("Settings", color="white"),
                    subtitle=ft.Text("Change password, email & more", color=COLOR_TEXT_MUTED, size=11),
                    on_click=lambda ev: open_settings_from_menu(dlg)
                ),
                ft.ListTile(
                    leading=ft.Icon(ft.Icons.BLOCK_ROUNDED, color=COLOR_DANGER),
                    title=ft.Text("Blocked Users", color="white"),
                    on_click=lambda ev: open_blocked_users_dialog(dlg)
                ),
                ft.ListTile(
                    leading=ft.Icon(ft.Icons.DESCRIPTION_ROUNDED, color=COLOR_TEXT_MUTED),
                    title=ft.Text("Terms & Privacy Policy", color="white"),
                    on_click=lambda ev: open_terms_dialog()
                ),
                ft.ListTile(
                    leading=ft.Icon(ft.Icons.LOGOUT_ROUNDED, color=COLOR_DANGER),
                    title=ft.Text("Log Out", color=COLOR_DANGER),
                    on_click=lambda ev: handle_logout_from_menu(dlg)
                ),
            ], tight=True, width=DIALOG_WIDTH),
            actions=[ft.TextButton("Close", on_click=lambda ev: close_menu_dialog(dlg))]
        )
        page.overlay.append(dlg)
        dlg.open = True
        page.update()

    def set_panel_visibility(feed=False, secrets=False, chats=False, people=False, reels=False, notifications=False, profile=False):
        if not chats:
            chat_state["polling_active"] = False
            chat_state["inbox_polling_active"] = False
        panel_home_feed.visible      = feed
        panel_whisper_wall.visible   = secrets
        panel_messages.visible       = chats
        panel_people.visible         = people
        panel_reels.visible          = reels
        panel_notifications.visible  = notifications
        panel_settings.visible       = profile
        panel_view_profile.visible   = False
        page.update()

    # --- NAVIGATION BAR (icon-based, Facebook-style) ---
    NAV_BTN_STYLE = ft.ButtonStyle(padding=6)
    nav_buttons = {
        "feed":    ft.IconButton(icon=ft.Icons.HOME_ROUNDED, icon_color=NAV_ACTIVE, tooltip="Feed", icon_size=20, style=NAV_BTN_STYLE),
        "secrets": ft.IconButton(icon=ft.Icons.THEATER_COMEDY_ROUNDED, icon_color=NAV_INACTIVE, tooltip="Secrets", icon_size=20, style=NAV_BTN_STYLE),
        "people":  ft.IconButton(icon=ft.Icons.GROUPS_ROUNDED, icon_color=NAV_INACTIVE, tooltip="Friends", icon_size=20, style=NAV_BTN_STYLE),
        "chats":   ft.IconButton(icon=ft.Icons.CHAT_BUBBLE_ROUNDED, icon_color=NAV_INACTIVE, tooltip="Chats", icon_size=20, style=NAV_BTN_STYLE),
        "reels":   ft.IconButton(icon=ft.Icons.VIDEO_LIBRARY_ROUNDED, icon_color=NAV_INACTIVE, tooltip="Reels", icon_size=20, style=NAV_BTN_STYLE),
        "notifications": ft.IconButton(icon=ft.Icons.NOTIFICATIONS_NONE_ROUNDED, icon_color=NAV_INACTIVE, tooltip="Notifications", icon_size=20, style=NAV_BTN_STYLE),
    }
    nav_buttons["feed"].on_click = nav_to_feed
    nav_buttons["secrets"].on_click = nav_to_secrets
    nav_buttons["people"].on_click = nav_to_people
    nav_buttons["chats"].on_click = nav_to_chats
    nav_buttons["reels"].on_click = nav_to_reels
    nav_buttons["notifications"].on_click = nav_to_notifications

    menu_button = ft.IconButton(icon=ft.Icons.MENU_ROUNDED, icon_color=NAV_INACTIVE, tooltip="Menu",
                                icon_size=20, style=NAV_BTN_STYLE, on_click=open_main_menu)

    # scroll=AUTO is a safety net — even on very narrow phones where icons
    # still don't all fit, every icon stays reachable by swiping sideways
    # instead of being invisibly pushed off-screen like before.
    custom_nav_bar = ft.Container(
        content=ft.Row([
            nav_buttons["feed"], nav_buttons["secrets"], nav_buttons["people"],
            nav_buttons["chats"], nav_buttons["reels"], nav_buttons["notifications"],
            menu_button
        ], alignment=ft.MainAxisAlignment.START, spacing=2, scroll=ft.ScrollMode.AUTO),
        padding=ft.Padding.symmetric(vertical=6),
        bgcolor=COLOR_CARD
    )

    # --- TAB 1: FEED & SEARCH ---
    public_text_box = ft.TextField(hint_text="What's happening on campus?", width=220, dense=True, color="white")
    search_input = ft.TextField(hint_text="Search by username...", width=260, dense=True, color="white", on_change=lambda e: render_friends_section(search_input.value))

    media_status_text = ft.Text("", size=11)
    selected_media = {"bytes": None, "name": None, "type": None}
    media_preview_container = ft.Container(visible=False)

    def clear_media_preview(e=None):
        selected_media["bytes"] = None
        selected_media["name"] = None
        selected_media["type"] = None
        media_preview_container.content = None
        media_preview_container.visible = False
        media_status_text.value = ""
        page.update()

    def show_media_preview():
        if selected_media["type"] == "image":
            try:
                import base64
                b64 = base64.b64encode(selected_media["bytes"]).decode("utf-8")
                preview_content = ft.Image(src_base64=b64, width=160, height=160,
                                           fit=ft.BoxFit.COVER, border_radius=RADIUS_MD)
            except Exception as ex:
                print(f"Preview render failed: {ex}")
                preview_content = ft.Icon(ft.Icons.IMAGE_ROUNDED, size=60, color=COLOR_PRIMARY)
        else:
            preview_content = ft.Column([
                ft.Icon(ft.Icons.PLAY_CIRCLE_ROUNDED, size=48, color="white"),
                ft.Text(selected_media["name"] or "video", color="white", size=11)
            ], alignment=ft.MainAxisAlignment.CENTER, horizontal_alignment=ft.CrossAxisAlignment.CENTER)

        media_preview_container.content = ft.Stack([
            ft.Container(content=preview_content, width=160, height=160,
                        bgcolor=COLOR_CARD, border_radius=RADIUS_MD, alignment=ft.Alignment.CENTER),
            ft.Container(
                content=ft.IconButton(icon=ft.Icons.CANCEL_ROUNDED, icon_color=COLOR_DANGER,
                                      icon_size=22, on_click=clear_media_preview),
                alignment=ft.Alignment.TOP_RIGHT
            )
        ], width=160, height=160)
        media_preview_container.visible = True
        page.update()

    async def open_media_picker(e):
        # with_data=True returns the file's raw bytes directly in f.bytes —
        # this works identically on web (where f.path is always None) and
        # on desktop, so we no longer need separate code paths per platform.
        files = await ft.FilePicker().pick_files(
            allow_multiple=False,
            file_type=ft.FilePickerFileType.CUSTOM,
            allowed_extensions=["jpg", "jpeg", "png", "gif", "webp", "mp4", "mov", "avi", "mkv", "webm"],
            with_data=True
        )
        if not files:
            page.update()
            return

        f = files[0]
        ext = os.path.splitext(f.name)[1].lower()
        if ext in IMAGE_EXTENSIONS:
            selected_media["type"] = "image"
        elif ext in VIDEO_EXTENSIONS:
            selected_media["type"] = "video"
        else:
            media_status_text.value = "Unsupported file type."
            media_status_text.color = COLOR_DANGER
            page.update()
            return

        if not f.bytes:
            media_status_text.value = "Couldn't read that file — try again."
            media_status_text.color = COLOR_DANGER
            page.update()
            return

        selected_media["bytes"] = f.bytes
        selected_media["name"] = f.name
        media_status_text.value = ""
        show_media_preview()  # Shows the actual picture/video card in the composer

    def reset_post_composer():
        public_text_box.value = ""
        selected_media["bytes"] = None
        selected_media["name"] = None
        selected_media["type"] = None
        media_status_text.value = ""
        media_preview_container.content = None
        media_preview_container.visible = False

    posting_spinner = ft.ProgressRing(width=16, height=16, stroke_width=2, visible=False)

    def set_composer_busy(is_busy):
        send_button.disabled = is_busy
        photo_button.disabled = is_busy
        posting_spinner.visible = is_busy
        page.update()

    def handle_create_post(e):
        text_content = (public_text_box.value or "").strip()
        if not text_content and not selected_media["bytes"]:
            media_status_text.value = "Write something or attach a photo/video first."
            media_status_text.color = COLOR_DANGER
            page.update()
            return

        set_composer_busy(True)
        media_status_text.value = "Posting..."
        media_status_text.color = COLOR_TEXT_MUTED
        page.update()

        media_url = None
        media_type = None
        try:
            user_id = get_cached_user_id()
            username = user_cache.get("username") or "Anonymous"

            if selected_media["bytes"]:
                raw_bytes = selected_media["bytes"]
                file_ext = os.path.splitext(selected_media["name"] or "")[1] or ".dat"
                owner_id = user_id if user_id else "anonymous"

                if selected_media["type"] == "image":
                    file_bytes, content_type = compress_image_for_upload(raw_bytes)
                    storage_path = f"{owner_id}/{uuid.uuid4()}.jpg"
                else:
                    file_bytes = raw_bytes
                    content_type = mimetypes.guess_type(selected_media["name"] or "")[0] or "application/octet-stream"
                    storage_path = f"{owner_id}/{uuid.uuid4()}{file_ext}"

                upload_with_retry(MEDIA_BUCKET, storage_path, file_bytes, content_type)
                media_url = supabase.storage.from_(MEDIA_BUCKET).get_public_url(storage_path)
                media_type = selected_media["type"]

            supabase.table("posts").insert({
                "user_id": user_id,
                "username": username,
                "content": text_content,
                "media_url": media_url,
                "media_type": media_type
            }).execute()

            reset_post_composer()
            set_composer_busy(False)
            render_public_feed()
        except Exception as ex:
            set_composer_busy(False)
            media_status_text.value = f"Post failed: {str(ex)}"
            media_status_text.color = COLOR_DANGER
            page.update()

    send_button = ft.IconButton(icon=ft.Icons.SEND_ROUNDED, icon_color=COLOR_PRIMARY, on_click=handle_create_post)
    photo_button = ft.IconButton(icon=ft.Icons.PHOTO_LIBRARY_ROUNDED, icon_color=COLOR_PRIMARY, tooltip="Add photo or video", on_click=open_media_picker)

    panel_home_feed = ft.Column([
        ft.Row([
            public_text_box,
            photo_button,
            send_button,
            posting_spinner
        ], alignment=ft.MainAxisAlignment.CENTER),
        media_preview_container,
        media_status_text,
        public_feed_layout
    ], visible=False, horizontal_alignment=ft.CrossAxisAlignment.CENTER)

    # --- PENDING CONNECTION REQUESTS BANNER (top of Friends tab) ---
    pending_requests_layout = ft.Column(spacing=6)
    pending_requests_banner = ft.Container(
        content=ft.Column([
            ft.Text("Connection Requests", size=13, weight=ft.FontWeight.BOLD, color=COLOR_WARNING),
            pending_requests_layout
        ], spacing=6),
        padding=SPACE_LG, bgcolor=COLOR_WHISPER, border_radius=RADIUS_MD, width=340, visible=False
    )

    def render_pending_requests_banner():
        reqs = get_pending_connection_requests()
        pending_requests_layout.controls.clear()
        if not reqs:
            pending_requests_banner.visible = False
            page.update()
            return
        pending_requests_banner.visible = True
        for r in reqs:
            def make_respond(request_id=r.get("request_id"), uname=r.get("requester_username", "Unknown")):
                def handler(accept):
                    def do_respond(e):
                        respond_connection_request(request_id, accept)
                        render_pending_requests_banner()
                        render_friends_section(search_input.value)
                    return do_respond
                return handler
            respond = make_respond()
            pending_requests_layout.controls.append(
                ft.Row([
                    ft.Text(f"@{r.get('requester_username', 'Unknown')} wants to connect",
                           color="white", size=12, expand=True),
                    ft.TextButton("Decline", on_click=respond(False)),
                    ft.TextButton("Accept", on_click=respond(True))
                ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN)
            )
        page.update()

    panel_people = ft.Column([
        ft.Text("Find Friends", size=18, weight=ft.FontWeight.BOLD, color="white"),
        pending_requests_banner,
        ft.Row([search_input, ft.Icon(ft.Icons.SEARCH_ROUNDED, color=COLOR_TEXT_MUTED)], alignment=ft.MainAxisAlignment.CENTER),
        friends_layout
    ], visible=False, horizontal_alignment=ft.CrossAxisAlignment.CENTER)

    # --- TAB 2: SECRETS ---
    whisper_text_box = ft.TextField(hint_text="Share a school secret anonymously...", width=260, dense=True, color="white")
    whisper_status_text = ft.Text("", size=11)
    creator_admin_switch = ft.Switch(value=False, on_change=lambda e: render_whisper_feed(reveal_names=creator_admin_switch.value))

    panel_whisper_wall = ft.Column([
        ft.Text("The Whisper Wall \U0001F92B", size=18, weight=ft.FontWeight.BOLD, color=COLOR_DANGER),
        ft.Row([ft.Text("Creator Key (Reveal Identity)", color="white"), creator_admin_switch], alignment=ft.MainAxisAlignment.CENTER),
        ft.Row([whisper_text_box, ft.IconButton(icon=ft.Icons.SEND_ROUNDED, icon_color=COLOR_DANGER, on_click=handle_post_whisper)], alignment=ft.MainAxisAlignment.CENTER),
        whisper_status_text,
        ft.Divider(height=10, color=COLOR_BORDER),
        whisper_feed_layout
    ], visible=False, horizontal_alignment=ft.CrossAxisAlignment.CENTER)

    # --- GLOBAL USER STATE CACHE ---
    # The sync Supabase client doesn't reliably persist sessions via set_session().
    # Instead, we cache the user's ID and email when they log in, and use that
    # throughout the app. This avoids the "not logged in" false negatives.
    user_cache = {"id": None, "email": None, "username": None, "access_token": None}

    def cache_user(user_obj, access_token=None):
        """Store the user's info and force the PostgREST client to use
        their JWT token — without this, RLS sees all requests as anonymous."""
        if user_obj:
            user_cache["id"] = user_obj.id
            user_cache["email"] = user_obj.email
            user_cache["access_token"] = access_token
            if access_token:
                # This is the critical line: forces ALL supabase.table() calls
                # to send the user's JWT in the Authorization header so RLS
                # recognises the request as coming from an authenticated user.
                supabase.postgrest.auth(access_token)
            # Fetch the REAL chosen username from profiles — never derive it
            # from the email, that was the bug causing emails to show on posts.
            refresh_cached_username(user_obj.id)
        else:
            user_cache["id"] = None
            user_cache["email"] = None
            user_cache["username"] = None
            user_cache["access_token"] = None

        # The active user just changed (logged in, logged out, or switched
        # accounts on the same device/session) — any per-user cache must be
        # thrown away here, or the next account can inherit stale data from
        # whoever was logged in before (e.g. blocked-user list bleeding into
        # a different account's Followers/Following view).
        blocked_ids_cache["ids"] = set()
        blocked_ids_cache["loaded"] = False

    def refresh_cached_username(user_id):
        try:
            resp = supabase.table("profiles").select("username").eq("user_id", user_id).execute()
            if resp.data and resp.data[0].get("username"):
                user_cache["username"] = resp.data[0]["username"]
            else:
                user_cache["username"] = "Unknown"
        except Exception as ex:
            print(f"Username refresh failed: {ex}")
            user_cache["username"] = "Unknown"

    def get_cached_user_id():
        """Return the cached user ID, or None if not logged in."""
        return user_cache["id"]

    def create_notification(recipient_id, notif_type, message, post_id=None):
        """Fires a notification via RPC. Silently skips if recipient is the
        actor themself (no self-notifications) or not logged in."""
        if not recipient_id or recipient_id == get_cached_user_id():
            return
        try:
            supabase.rpc("create_notification", {
                "p_recipient_id": recipient_id,
                "p_actor_username": user_cache.get("username", "Someone"),
                "p_type": notif_type,
                "p_message": message,
                "p_post_id": post_id
            }).execute()
        except Exception as ex:
            print(f"Notification create error: {ex}")

    # --- BLOCK / REPORT (safety) ---
    blocked_ids_cache = {"ids": set(), "loaded": False}

    def get_blocked_ids(force_refresh=False):
        """Returns a set of user_ids the current user has blocked. Cached
        per-session; call with force_refresh=True right after blocking/unblocking."""
        user_id = get_cached_user_id()
        if not user_id:
            return set()
        if blocked_ids_cache["loaded"] and not force_refresh:
            return blocked_ids_cache["ids"]
        try:
            resp = supabase.rpc("get_blocked_user_ids", {"p_user_id": user_id}).execute()
            blocked_ids_cache["ids"] = {row["blocked_id"] for row in (resp.data or [])}
            blocked_ids_cache["loaded"] = True
        except Exception as ex:
            print(f"get_blocked_ids error: {ex}")
        return blocked_ids_cache["ids"]

    def block_user_action(target_user_id):
        user_id = get_cached_user_id()
        if not user_id or not target_user_id or target_user_id == user_id:
            return False
        try:
            supabase.rpc("block_user", {"p_blocker_id": user_id, "p_blocked_id": target_user_id}).execute()
            get_blocked_ids(force_refresh=True)
            return True
        except Exception as ex:
            print(f"Block error: {ex}")
            return False

    def unblock_user_action(target_user_id):
        user_id = get_cached_user_id()
        if not user_id:
            return False
        try:
            supabase.rpc("unblock_user", {"p_blocker_id": user_id, "p_blocked_id": target_user_id}).execute()
            get_blocked_ids(force_refresh=True)
            return True
        except Exception as ex:
            print(f"Unblock error: {ex}")
            return False

    def report_post_action(post_id, reason):
        user_id = get_cached_user_id()
        if not user_id:
            return False
        try:
            supabase.rpc("report_post", {
                "p_post_id": post_id, "p_reporter_id": user_id, "p_reason": reason
            }).execute()
            return True
        except Exception as ex:
            print(f"Report post error: {ex}")
            return False

    def report_user_action(target_user_id, reason):
        user_id = get_cached_user_id()
        if not user_id:
            return False
        try:
            supabase.rpc("report_user", {
                "p_reported_user_id": target_user_id, "p_reporter_id": user_id, "p_reason": reason
            }).execute()
            return True
        except Exception as ex:
            print(f"Report user error: {ex}")
            return False

    # --- CONNECTIONS (Add Friend / Accept / Pending) ---
    def send_connection_request(target_user_id):
        user_id = get_cached_user_id()
        if not user_id or not target_user_id:
            return None, "You must be logged in."
        try:
            resp = supabase.rpc("send_connection_request", {
                "p_requester_id": user_id,
                "p_recipient_id": target_user_id
            }).execute()
            return resp.data, None
        except Exception as ex:
            return None, f"Couldn't send request: {str(ex)}"

    def respond_connection_request(request_id, accept):
        user_id = get_cached_user_id()
        if not user_id:
            return None, "You must be logged in."
        try:
            resp = supabase.rpc("respond_connection_request", {
                "p_request_id": request_id,
                "p_user_id": user_id,
                "p_accept": accept
            }).execute()
            return resp.data, None
        except Exception as ex:
            return None, f"Couldn't respond: {str(ex)}"

    def get_connection_status(other_user_id):
        """Returns (status, request_id, is_requester) or (None, None, None) if
        no connection exists yet between the current user and other_user_id."""
        user_id = get_cached_user_id()
        if not user_id or not other_user_id:
            return None, None, None
        try:
            resp = supabase.rpc("get_connection_status", {
                "p_user_id": user_id,
                "p_other_user_id": other_user_id
            }).execute()
            if resp.data:
                row = resp.data[0]
                return row.get("status"), row.get("request_id"), row.get("is_requester")
        except Exception as ex:
            print(f"get_connection_status error: {ex}")
        return None, None, None

    def get_pending_connection_requests():
        user_id = get_cached_user_id()
        if not user_id:
            return []
        try:
            resp = supabase.rpc("get_pending_connection_requests", {"p_user_id": user_id}).execute()
            return resp.data or []
        except Exception as ex:
            print(f"get_pending_connection_requests error: {ex}")
            return []

    # ============================================================
    # --- CONNECTIONS DATA LAYER --------------------------------
    # Single source of truth for reading the `connections` table. Every
    # feature that needs connection rows (Find Friends badges, Followers/
    # Following counts, the Followers/Following list) goes through
    # fetch_my_connection_rows() below instead of writing its own query.
    # That gives us one place to get the direction-handling and
    # deduplication right, instead of N slightly-different queries that
    # can silently drift out of sync with each other.
    # ============================================================
    def fetch_my_connection_rows(user_id, status=None):
        """Returns every connection row involving user_id, as a list of
        {id, requester_id, recipient_id, status} dicts — or None if the
        fetch itself failed (as opposed to succeeding with zero rows).
        That distinction matters: a caller must never treat a network/DB
        error as "this user has no connections".

        Symmetric by construction: a `connections` row can have the user
        on EITHER side (requester_id or recipient_id), so this issues two
        explicit, independently-filtered queries — one per side — rather
        than a single combined OR filter, then merges the results. This
        makes each half of the relationship individually verifiable and
        keeps the status filter (when given) applied identically on both
        sides, instead of leaning on `.or_()` string-filter composition.

        Deduplicates by row id, so a row can never be counted twice even
        if both queries somehow returned it (e.g. malformed data where
        requester_id == recipient_id).
        """
        if not user_id:
            return []
        try:
            requester_query = supabase.table("connections") \
                .select("id, requester_id, recipient_id, status") \
                .eq("requester_id", user_id)
            recipient_query = supabase.table("connections") \
                .select("id, requester_id, recipient_id, status") \
                .eq("recipient_id", user_id)
            if status:
                requester_query = requester_query.eq("status", status)
                recipient_query = recipient_query.eq("status", status)

            as_requester = requester_query.execute()
            as_recipient = recipient_query.execute()
            rows = (as_requester.data or []) + (as_recipient.data or [])

            deduped_by_row_id = {}
            for r in rows:
                rid = r.get("id")
                if rid is None:
                    continue  # malformed row — skip rather than crash
                deduped_by_row_id[rid] = r
            return list(deduped_by_row_id.values())
        except Exception as ex:
            print(f"fetch_my_connection_rows error: {ex}")
            return None  # distinct from [] — signals "couldn't determine", not "zero"

    def get_my_accepted_connections():
        """Returns {other_user_id: connection_row_id} for every ACCEPTED
        connection involving the current user, or None if the underlying
        fetch failed. Deduplicates by the OTHER participant's id (not just
        row id) so the count always matches the number of distinct people
        the user is actually connected to, even in the unlikely event of
        a duplicate row for the same pair."""
        user_id = get_cached_user_id()
        if not user_id:
            return {}
        rows = fetch_my_connection_rows(user_id, status="accepted")
        if rows is None:
            return None  # propagate "fetch failed" — do not fabricate an empty result
        result = {}
        for row in rows:
            requester = row.get("requester_id")
            recipient = row.get("recipient_id")
            if not requester or not recipient:
                continue  # malformed row — skip rather than crash
            if requester == recipient:
                continue  # defensive: a connection can't be with yourself
            other = recipient if requester == user_id else requester
            if not other or other == user_id:
                continue
            result[other] = row.get("id")
        return result

    def get_my_connections_map():
        """One entry per connection the current user has (any status),
        keyed by the OTHER person's id. Used to label the + button on
        every row in Find Friends in a single round trip. Returns {} both
        when there are genuinely no connections AND when the fetch failed
        — this map only ever adds a badge, so failing open (no badge) is
        the safe default; the stats row and Followers/Following list are
        what carry the stronger "don't show a false 0" guarantee."""
        user_id = get_cached_user_id()
        if not user_id:
            return {}
        rows = fetch_my_connection_rows(user_id)
        if rows is None:
            return {}
        result = {}
        for row in rows:
            requester = row.get("requester_id")
            recipient = row.get("recipient_id")
            if not requester or not recipient or requester == recipient:
                continue
            other = recipient if requester == user_id else requester
            result[other] = {
                "status": row.get("status"),
                "request_id": row.get("id"),
                "is_requester": requester == user_id
            }
        return result

    def open_respond_dialog(request_id, requester_username, on_responded=None):
        """Shared Accept/Decline dialog — used from the profile page, the
        Find Friends + button, and anywhere else a single incoming request
        needs a quick response."""
        def close_dlg(d):
            d.open = False
            page.update()

        def do_respond(accept):
            def handler(ev):
                result, error = respond_connection_request(request_id, accept)
                close_dlg(dlg)
                if on_responded:
                    on_responded(accept, error)
            return handler

        dlg = ft.AlertDialog(
            title=ft.Text(f"@{requester_username} wants to connect", color="white", size=15),
            bgcolor=COLOR_CARD,
            content=ft.Text("Accept to chat freely, or decline the request.", color=COLOR_TEXT_MUTED, size=13),
            actions=[
                ft.TextButton("Decline", on_click=do_respond(False)),
                ft.ElevatedButton("Accept", bgcolor=COLOR_SUCCESS, on_click=do_respond(True)),
                ft.TextButton("Close", on_click=lambda ev: close_dlg(dlg))
            ]
        )
        page.overlay.append(dlg)
        dlg.open = True
        page.update()

    def get_conversations():
        user_id = get_cached_user_id()
        if not user_id:
            return []
        try:
            resp = supabase.rpc("get_user_conversations", {
                "p_user_id": user_id
            }).execute()
            return resp.data or []
        except Exception as e:
            print(f"Error fetching conversations: {e}")
            return []

    def get_or_create_conversation(target_username):
        user_id = get_cached_user_id()
        if not user_id:
            return None, "You must be logged in."
        try:
            # Normalize what the person typed — they may add "@" out of habit,
            # or type the username in different case than it was saved. The
            # Friends tab never has this problem because it hands back the
            # exact stored username, but typing it by hand needs to match
            # loosely the same way any login/search field would.
            cleaned_username = (target_username or "").strip().lstrip("@")

            # Look up the target user's profile (case-insensitive, exact match —
            # ilike with no % wildcards behaves like a case-insensitive eq)
            profile_resp = supabase.table("profiles").select("user_id, username").ilike("username", cleaned_username).execute()
            if not profile_resp.data:
                return None, f"No user found with username '{cleaned_username}'."
            target_uid = profile_resp.data[0]["user_id"]

            if not target_uid:
                return None, "That user hasn't finished setting up their profile yet."
            if target_uid == user_id:
                return None, "You can't start a chat with yourself."
            if target_uid in get_blocked_ids():
                return None, "You've blocked this user. Unblock them in the Menu to message them again."

            # Use a SECURITY DEFINER database function to create the conversation.
            # This bypasses RLS entirely so the sync client's JWT issue doesn't matter.
            result = supabase.rpc("create_conversation_between", {
                "p_user1": user_id,
                "p_user2": target_uid
            }).execute()

            if result.data:
                return result.data, None
            else:
                return None, "Couldn't create conversation — check Supabase logs."
        except Exception as e:
            return None, f"Couldn't start chat: {str(e)}"

    def get_messages(conversation_id):
        try:
            resp = supabase.rpc("get_conversation_messages", {
                "p_conversation_id": conversation_id
            }).execute()
            return resp.data or []
        except Exception as e:
            print(f"Error fetching messages: {e}")
            return []

    def send_message(conversation_id, content):
        user_id = get_cached_user_id()
        if not user_id or not content.strip():
            return False, None
        try:
            supabase.rpc("send_chat_message", {
                "p_conversation_id": conversation_id,
                "p_sender_id": user_id,
                "p_content": content.strip()
            }).execute()
            # Notify the other participant(s) in this conversation
            try:
                parts = supabase.rpc("get_conversation_participant_ids", {
                    "p_conversation_id": conversation_id
                }).execute()
                for part in (parts.data or []):
                    other_id = part.get("user_id")
                    if other_id and other_id != user_id:
                        create_notification(other_id, "message",
                                            f"{user_cache.get('username','Someone')} sent you a message")
            except Exception as notif_ex:
                print(f"Message notification error: {notif_ex}")
            return True, None
        except Exception as e:
            msg = str(e)
            if "CONNECTION_REQUIRED" in msg:
                return False, "You've sent your one message — you can chat freely once they accept your connection request."
            print(f"Error sending message: {e}")
            return False, None

    def format_relative_time(iso_str):
        """Turns a Postgres timestamptz string into a short relative label
        like 'now', '5m ago', '3h ago', '2d ago', or a date for older messages."""
        if not iso_str:
            return ""
        try:
            ts = datetime.fromisoformat(str(iso_str).replace("Z", "+00:00"))
            if ts.tzinfo is None:
                ts = ts.replace(tzinfo=timezone.utc)
            now = datetime.now(timezone.utc)
            seconds = (now - ts).total_seconds()
            if seconds < 0:
                seconds = 0
            if seconds < 60:
                return "now"
            elif seconds < 3600:
                return f"{int(seconds // 60)}m ago"
            elif seconds < 86400:
                return f"{int(seconds // 3600)}h ago"
            elif seconds < 604800:
                return f"{int(seconds // 86400)}d ago"
            else:
                return ts.strftime("%b %d")
        except Exception as ex:
            print(f"Time format error: {ex}")
            return ""

    def conversations_signature(convs):
        """Cheap fingerprint of the inbox list — lets the poller skip
        re-rendering (and the visual flicker that comes with it) when
        nothing has actually changed since the last check."""
        return tuple(
            (c.get("conversation_id"), c.get("last_message"), c.get("last_message_at"))
            for c in convs
        )

    chat_state = {"conversation_id": None, "other_username": None, "polling_active": False, "last_rendered_count": -1,
                  "inbox_polling_active": False, "last_inbox_signature": None}

    conversations_layout = ft.Column(spacing=8, scroll=ft.ScrollMode.ALWAYS, height=260)
    new_chat_input = ft.TextField(hint_text="Start a chat (enter username)", width=220, dense=True, color="white")
    chat_inbox_status = ft.Text("", size=12)

    thread_messages_layout = ft.Column(spacing=8, scroll=ft.ScrollMode.ALWAYS, height=260, auto_scroll=True)
    thread_input_box = ft.TextField(hint_text="Type a message...", width=220, dense=True, color="white")
    thread_header_text = ft.Text("", size=16, weight=ft.FontWeight.BOLD, color="white")
    thread_status = ft.Text("", size=11)

    def render_conversations_list(force=False):
        convs = get_conversations()  # already sorted newest-first by the DB function
        sig = conversations_signature(convs)
        if not force and sig == chat_state["last_inbox_signature"]:
            return  # nothing changed since the last poll — skip the redraw
        chat_state["last_inbox_signature"] = sig

        conversations_layout.controls.clear()
        if not convs:
            conversations_layout.controls.append(ft.Text("No chats yet. Start one below!", color=COLOR_TEXT_MUTED, size=12))
        for c in convs:
            def open_this(e, cid=c["conversation_id"], uname=c["other_username"]):
                open_thread(cid, uname)

            time_label = format_relative_time(c.get("last_message_at"))

            conversations_layout.controls.append(
                ft.Container(
                    content=ft.Row([
                        ft.Column([
                            ft.Text(c["other_username"], weight=ft.FontWeight.BOLD, color=COLOR_SUCCESS, size=14),
                            ft.Text(c["last_message"], color=COLOR_TEXT_BODY, size=12, max_lines=1)
                        ], spacing=2, expand=True),
                        ft.Text(time_label, color=COLOR_TEXT_FAINT, size=10)
                    ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                    padding=SPACE_LG, bgcolor=COLOR_CARD, border_radius=RADIUS_MD, width=320,
                    on_click=open_this
                )
            )
        page.update()

    async def poll_inbox_loop():
        while chat_state["inbox_polling_active"]:
            await asyncio.sleep(3)
            if not chat_state["inbox_polling_active"]:
                break
            render_conversations_list()

    def handle_start_new_chat(e):
        target = (new_chat_input.value or "").strip()
        if not target:
            chat_inbox_status.value = "Enter a username first."
            chat_inbox_status.color = COLOR_DANGER
            page.update()
            return
        conv_id, error = get_or_create_conversation(target)
        if error:
            chat_inbox_status.value = error
            chat_inbox_status.color = COLOR_DANGER
            page.update()
            return
        new_chat_input.value = ""
        chat_inbox_status.value = ""
        render_conversations_list()
        open_thread(conv_id, target)

    def render_thread_messages():
        messages = get_messages(chat_state["conversation_id"])
        if len(messages) == chat_state["last_rendered_count"]:
            return
        chat_state["last_rendered_count"] = len(messages)

        thread_messages_layout.controls.clear()
        my_id = get_cached_user_id()
        for m in messages:
            is_mine = m.get("sender_id") == my_id
            bubble_color = COLOR_PRIMARY if is_mine else COLOR_CARD
            align = ft.MainAxisAlignment.END if is_mine else ft.MainAxisAlignment.START
            time_label = format_relative_time(m.get("created_at"))
            thread_messages_layout.controls.append(
                ft.Row([
                    ft.Column([
                        ft.Container(
                            content=ft.Text(m.get("content", ""), color="white", size=13),
                            padding=SPACE_MD, bgcolor=bubble_color, border_radius=RADIUS_LG, width=220
                        ),
                        ft.Text(time_label, color=COLOR_TEXT_FAINT, size=9)
                    ], spacing=2,
                       horizontal_alignment=ft.CrossAxisAlignment.END if is_mine else ft.CrossAxisAlignment.START)
                ], alignment=align)
            )
        page.update()

    async def poll_messages_loop():
        while chat_state["polling_active"]:
            await asyncio.sleep(2.5)
            if not chat_state["polling_active"]:
                break
            render_thread_messages()

    def open_thread(conversation_id, other_username):
        chat_state["inbox_polling_active"] = False  # only one poller needs to run at a time
        chat_state["conversation_id"] = conversation_id
        chat_state["other_username"] = other_username
        chat_state["last_rendered_count"] = -1
        thread_header_text.value = other_username
        thread_status.value = ""
        panel_chats_inbox.visible = False
        panel_chats_thread.visible = True
        page.update()
        render_thread_messages()
        chat_state["polling_active"] = True
        page.run_task(poll_messages_loop)

    def close_thread(e):
        chat_state["polling_active"] = False
        chat_state["conversation_id"] = None
        panel_chats_thread.visible = False
        panel_chats_inbox.visible = True
        render_conversations_list(force=True)
        chat_state["inbox_polling_active"] = True
        page.run_task(poll_inbox_loop)
        page.update()

    def handle_send_thread_message(e):
        content = thread_input_box.value or ""
        if not content.strip():
            return
        sent_ok, send_err = send_message(chat_state["conversation_id"], content)
        if sent_ok:
            thread_input_box.value = ""
            thread_status.value = ""
            page.update()
            render_thread_messages()
        else:
            thread_status.value = send_err or "Message failed to send."
            thread_status.color = COLOR_WARNING if send_err else COLOR_DANGER
            page.update()

    panel_chats_inbox = ft.Column([
        ft.Text("Direct Messages \U0001F4AC", size=18, weight=ft.FontWeight.BOLD, color=COLOR_SUCCESS),
        ft.Row([new_chat_input, ft.IconButton(icon=ft.Icons.SEND_ROUNDED, icon_color=COLOR_SUCCESS, on_click=handle_start_new_chat)], alignment=ft.MainAxisAlignment.CENTER),
        chat_inbox_status,
        ft.Divider(height=10, color=COLOR_BORDER),
        conversations_layout
    ], visible=True, horizontal_alignment=ft.CrossAxisAlignment.CENTER)

    QUICK_EMOJIS = [
        "😀", "😂", "😍", "😘", "😊", "😉", "😢", "😭", "😡", "😱",
        "👍", "👎", "👏", "🙏", "🙌", "💪", "🤝", "✌️", "🤞", "👌",
        "❤️", "🔥", "💯", "🎉", "😴", "🤔", "😎", "🥺", "😅", "🙄",
        "💀", "👀", "🤣", "😩", "🥳", "😏", "🤗", "😬", "😤", "💔"
    ]

    def open_emoji_picker(target_field):
        def insert_emoji(emoji):
            def handler(e):
                target_field.value = (target_field.value or "") + emoji
                close_dlg(dlg)
                page.update()
            return handler

        def close_dlg(d):
            d.open = False
            page.update()

        grid = ft.GridView(
            expand=False, runs_count=8, max_extent=40,
            spacing=4, run_spacing=4, height=220, width=DIALOG_WIDTH
        )
        for em in QUICK_EMOJIS:
            grid.controls.append(
                ft.TextButton(content=ft.Text(em, size=20), on_click=insert_emoji(em))
            )

        dlg = ft.AlertDialog(
            title=ft.Text("Emoji", color="white", size=14),
            bgcolor=COLOR_CARD,
            content=grid,
            actions=[ft.TextButton("Close", on_click=lambda e: close_dlg(dlg))]
        )
        page.overlay.append(dlg)
        dlg.open = True
        page.update()

    panel_chats_thread = ft.Column([
        ft.Row([
            ft.IconButton(icon=ft.Icons.ARROW_BACK_ROUNDED, icon_color=COLOR_SUCCESS, on_click=close_thread),
            thread_header_text
        ], alignment=ft.MainAxisAlignment.START),
        thread_messages_layout,
        thread_status,
        ft.Row([
            thread_input_box,
            ft.IconButton(icon=ft.Icons.EMOJI_EMOTIONS_ROUNDED, icon_color=COLOR_TEXT_MUTED,
                          tooltip="Emoji", on_click=lambda e: open_emoji_picker(thread_input_box)),
            ft.IconButton(icon=ft.Icons.SEND_ROUNDED, icon_color=COLOR_SUCCESS, on_click=handle_send_thread_message)
        ], alignment=ft.MainAxisAlignment.CENTER)
    ], visible=False, horizontal_alignment=ft.CrossAxisAlignment.CENTER)

    panel_messages = ft.Column([panel_chats_inbox, panel_chats_thread], visible=False, horizontal_alignment=ft.CrossAxisAlignment.CENTER)

    # --- TAB 4: PROFILE ---
    async def handle_logout(e):
        try:
            supabase.auth.sign_out()
        except Exception as ex:
            print(f"Sign out error: {ex}")
        cache_user(None)
        await clear_session()
        show_auth()

    # --- PROFILE HELPER: editable dropdown (pick from list OR type any custom value) ---
    def make_editable_dd(label, options, width=300):
        return ft.Dropdown(
            label=label, width=width, color="white", editable=True,
            enable_filter=True,
            options=[ft.dropdown.Option(o) for o in options]
        )

    def get_dd_value(dd):
        return (dd.value or "").strip() or None

    def set_dd_value(dd, value):
        dd.value = value or None

    # --- PROFILE FIELDS (own profile editing) ---
    profile_status_text = ft.Text("", size=12)
    profile_avatar_img = ft.Image(
        src="https://ui-avatars.com/api/?background=6366f1&color=fff&size=80&name=U",
        width=80, height=80, fit=ft.BoxFit.COVER, border_radius=40
    )
    profile_username_label = ft.Text("", size=15, weight=ft.FontWeight.BOLD, color=COLOR_PRIMARY)
    profile_bio = ft.TextField(label="Bio (optional)", width=300, color="white",
                               multiline=True, max_lines=3, border_color=COLOR_PRIMARY)
    profile_school = ft.TextField(label="School / University", width=300,
                                  color="white", border_color=COLOR_PRIMARY)
    profile_password = ft.TextField(label="New Password (leave blank to keep)", password=True,
                                    width=300, color="white", border_color=COLOR_PRIMARY)

    dept_dd = make_editable_dd("Department", DEPARTMENTS)
    country_dd = make_editable_dd("Country", COUNTRIES)
    state_dd = make_editable_dd("State", NIGERIAN_STATES)
    lga_dd = make_editable_dd("Local Government", [])  # populated once a state is picked

    def on_state_change(e):
        selected_state = state_dd.value
        lga_list = NIGERIA_LGAS_BY_STATE.get(selected_state, [])
        lga_dd.options = [ft.dropdown.Option(o) for o in lga_list]
        lga_dd.value = None  # reset LGA when state changes
        page.update()
    state_dd.on_change = on_state_change

    # --- ACCOUNT SETTINGS (email/password) — separate from main profile ---
    profile_password = ft.TextField(label="Change Password", password=True,
                                    width=280, color="white", border_color=COLOR_PRIMARY)
    settings_email = ft.TextField(label="Change Email", width=280,
                                  color="white", border_color=COLOR_PRIMARY)
    settings_status = ft.Text("", size=12)

    def handle_save_account_settings(e):
        try:
            updates = {}
            new_email = None
            if settings_email.value and settings_email.value.strip():
                new_email = settings_email.value.strip()
                updates["email"] = new_email
            if profile_password.value and profile_password.value.strip():
                updates["password"] = profile_password.value.strip()
            if updates:
                supabase.auth.update_user(updates)
                if new_email:
                    # Keep profiles.email in sync — username login depends on this
                    user_id = get_cached_user_id()
                    if user_id:
                        supabase.table("profiles").update({"email": new_email}).eq("user_id", user_id).execute()
                    user_cache["email"] = new_email
                profile_password.value = ""
                settings_status.value = "Account updated! ✅"
                settings_status.color = COLOR_SUCCESS
            else:
                settings_status.value = "Nothing to update."
                settings_status.color = COLOR_TEXT_MUTED
            page.update()
        except Exception as ex:
            settings_status.value = f"Update failed: {str(ex)}"
            settings_status.color = COLOR_DANGER
            page.update()

    def close_settings_dialog(d):
        d.open = False
        page.update()

    def open_account_settings(e):
        settings_email.value = user_cache.get("email", "")
        settings_status.value = ""
        dlg = ft.AlertDialog(
            title=ft.Text("Account Settings", color="white", size=16),
            bgcolor=COLOR_CARD,
            content=ft.Column([
                settings_email,
                profile_password,
                settings_status
            ], tight=True, spacing=12, width=DIALOG_WIDTH),
            actions=[
                ft.TextButton("Save", on_click=handle_save_account_settings),
                ft.TextButton("Close", on_click=lambda ev: close_settings_dialog(dlg))
            ]
        )
        page.overlay.append(dlg)
        dlg.open = True
        page.update()


    # --- PROFILE STATS ROW (Posts / Followers / Following / Total Likes) ---
    def format_count(n):
        """Renders a stat count. None means 'we don't actually know this
        value' (a failed fetch) and must never be silently shown as 0 —
        that's the exact bug that made real friends look like they'd
        vanished. None renders as an em dash instead."""
        if n is None:
            return "—"
        try:
            n = int(n)
        except Exception:
            return "—"
        if n >= 1_000_000:
            return f"{n / 1_000_000:.1f}".rstrip("0").rstrip(".") + "M"
        if n >= 1_000:
            return f"{n / 1_000:.1f}".rstrip("0").rstrip(".") + "K"
        return str(n)

    profile_stat_posts = ft.Text("0", size=20, weight=ft.FontWeight.BOLD, color="white")
    profile_stat_followers = ft.Text("0", size=20, weight=ft.FontWeight.BOLD, color="white")
    profile_stat_following = ft.Text("0", size=20, weight=ft.FontWeight.BOLD, color="white")
    profile_stat_likes = ft.Text("0", size=20, weight=ft.FontWeight.BOLD, color="white")

    def make_stat_column(value_text, label, on_click=None):
        col = ft.Column(
            [value_text, ft.Text(label, color=COLOR_TEXT_MUTED, size=11)],
            spacing=2, horizontal_alignment=ft.CrossAxisAlignment.CENTER
        )
        if on_click:
            return ft.Container(content=col, on_click=on_click, ink=True,
                               border_radius=RADIUS_SM, padding=4)
        return col

    # --- FOLLOWERS / FOLLOWING LIST (backed by accepted connections) ---
    def get_my_connection_users():
        """Returns [{user_id, username, avatar_url, request_id}, ...] for every
        user the current user has an accepted connection with, minus anyone
        blocked. Returns None (not []) if the fetch itself failed, so callers
        can show "couldn't load" instead of a misleading "no connections"."""
        user_id = get_cached_user_id()
        if not user_id:
            return []
        try:
            # Single source of truth: the same accepted-connections lookup
            # used by the stats counters, so the list and the numbers can
            # never drift apart from each other.
            accepted = get_my_accepted_connections()  # {other_user_id: request_id}, or None on failure
            if accepted is None:
                return None
            blocked = get_blocked_ids()
            other_ids = [uid for uid in accepted.keys() if uid not in blocked]
            if not other_ids:
                return []
            profiles_resp = supabase.table("profiles") \
                .select("user_id, username, avatar_url").in_("user_id", other_ids).execute()
            results = []
            for pr in (profiles_resp.data or []):
                results.append({
                    "user_id": pr["user_id"],
                    "username": pr.get("username") or "Unknown",
                    "avatar_url": pr.get("avatar_url"),
                    "request_id": accepted.get(pr["user_id"])
                })
            return results
        except Exception as ex:
            print(f"get_my_connection_users error: {ex}")
            return None

    def remove_connection_action(request_id):
        try:
            supabase.table("connections").delete().eq("id", request_id).execute()
            return True
        except Exception as ex:
            print(f"remove_connection_action error: {ex}")
            return False

    def open_connections_list_dialog(title="Connections"):
        list_col = ft.Column(spacing=8, scroll=ft.ScrollMode.AUTO, height=320, width=DIALOG_WIDTH)
        status = ft.Text("", size=11)

        def close_dlg(d):
            d.open = False
            page.update()

        def confirm_action(prompt, on_confirm):
            """Small yes/no guard shown before any destructive action
            (unfollow/block) actually runs — prevents a stray tap in the
            list from silently removing a real connection."""
            def do_confirm(ev):
                confirm_dlg.open = False
                page.update()
                on_confirm()

            def do_cancel(ev):
                confirm_dlg.open = False
                page.update()

            confirm_dlg = ft.AlertDialog(
                title=ft.Text("Are you sure?", color="white", size=15),
                bgcolor=COLOR_CARD,
                content=ft.Text(prompt, color=COLOR_TEXT_BODY, size=13),
                actions=[
                    ft.TextButton("Cancel", on_click=do_cancel),
                    ft.TextButton("Confirm", on_click=do_confirm),
                ]
            )
            page.overlay.append(confirm_dlg)
            confirm_dlg.open = True
            page.update()

        def load_list():
            list_col.controls.clear()
            users = get_my_connection_users()
            if users is None:
                list_col.controls.append(
                    ft.Text("Couldn't load your connections — check your connection and try again.",
                           color=COLOR_DANGER, size=12)
                )
                page.update()
                return
            if not users:
                list_col.controls.append(ft.Text("No connections yet.", color=COLOR_TEXT_MUTED, size=12))
                page.update()
                return
            for u in users:
                def make_view(name=u["username"]):
                    def handler(e):
                        close_dlg(dlg)
                        load_other_profile(name)
                    return handler

                def make_unfollow(req_id=u["request_id"], uname=u["username"]):
                    def do_remove():
                        if remove_connection_action(req_id):
                            status.value = f"Removed @{uname}."
                            status.color = COLOR_SUCCESS
                            stats = get_my_stats()
                            profile_stat_followers.value = format_count(stats["followers"])
                            profile_stat_following.value = format_count(stats["following"])
                        else:
                            status.value = "Couldn't remove — try again."
                            status.color = COLOR_DANGER
                        load_list()
                        page.update()

                    def handler(e):
                        confirm_action(f"Remove @{uname} from your connections?", do_remove)
                    return handler

                def make_block(target_id=u["user_id"], uname=u["username"]):
                    def do_block():
                        if block_user_action(target_id):
                            status.value = f"Blocked @{uname}."
                            status.color = COLOR_SUCCESS
                            stats = get_my_stats()
                            profile_stat_followers.value = format_count(stats["followers"])
                            profile_stat_following.value = format_count(stats["following"])
                        else:
                            status.value = "Couldn't block — try again."
                            status.color = COLOR_DANGER
                        load_list()
                        page.update()

                    def handler(e):
                        confirm_action(f"Block @{uname}? They won't be able to see or message you.", do_block)
                    return handler

                list_col.controls.append(
                    ft.Row([
                        ft.Text(f"@{u['username']}", color="white", size=13, expand=True),
                        ft.IconButton(icon=ft.Icons.PERSON_ROUNDED, icon_color=COLOR_PRIMARY,
                                     tooltip="View profile", icon_size=18, on_click=make_view()),
                        ft.IconButton(icon=ft.Icons.PERSON_REMOVE_ROUNDED, icon_color=COLOR_WARNING,
                                     tooltip="Unfollow", icon_size=18, on_click=make_unfollow()),
                        ft.IconButton(icon=ft.Icons.BLOCK_ROUNDED, icon_color=COLOR_DANGER,
                                     tooltip="Block", icon_size=18, on_click=make_block()),
                    ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN)
                )
            page.update()

        dlg = ft.AlertDialog(
            title=ft.Text(title, color="white", size=16),
            bgcolor=COLOR_CARD,
            content=ft.Column([list_col, status], tight=True, spacing=8),
            actions=[ft.TextButton("Close", on_click=lambda ev: close_dlg(dlg))]
        )
        page.overlay.append(dlg)
        dlg.open = True
        load_list()
        page.update()


    profile_stats_row = ft.Container(
        content=ft.Row([
            make_stat_column(profile_stat_posts, "Posts"),
            make_stat_column(profile_stat_followers, "Followers",
                            on_click=lambda e: open_connections_list_dialog("Followers")),
            make_stat_column(profile_stat_following, "Following",
                            on_click=lambda e: open_connections_list_dialog("Following")),
            make_stat_column(profile_stat_likes, "Total Likes"),
        ], alignment=ft.MainAxisAlignment.SPACE_EVENLY),
        padding=SPACE_LG, bgcolor=COLOR_CARD, border_radius=RADIUS_MD, width=340
    )

    def get_my_stats():
        """Returns {posts, followers, following, likes}. Any value this
        function couldn't actually determine is None, never a fabricated
        0 — callers (via format_count) render that as '—' so a network
        hiccup can never masquerade as 'you have 0 friends'."""
        user_id = get_cached_user_id()
        stats = {"posts": None, "followers": None, "following": None, "likes": None}
        if not user_id:
            return stats
        try:
            posts_resp = supabase.table("posts").select("id", count="exact").eq("user_id", user_id).execute()
            stats["posts"] = posts_resp.count if posts_resp.count is not None else len(posts_resp.data or [])
        except Exception as ex:
            print(f"stats posts error: {ex}")
        try:
            # Same data layer as the Followers/Following list dialog and the
            # Find Friends badges — one accepted-connections source of truth,
            # so the number on the stats row can never drift from the list
            # you see when you tap it.
            accepted = get_my_accepted_connections()
            if accepted is None:
                stats["followers"] = None
                stats["following"] = None
            else:
                conn_count = len(accepted)
                stats["followers"] = conn_count
                stats["following"] = conn_count
        except Exception as ex:
            print(f"stats connections error: {ex}")
        try:
            my_ids_resp = supabase.table("posts").select("id").eq("user_id", user_id).execute()
            ids = [r["id"] for r in (my_ids_resp.data or [])]
            likes_map = get_likes_map(ids)
            stats["likes"] = sum(v.get("like_count", 0) for v in likes_map.values())
        except Exception as ex:
            print(f"stats likes error: {ex}")
        return stats

    # --- MY POSTS SECTION (tab nav + content grid) ---
    CARD_ACCENT_COLORS = [COLOR_WARNING, COLOR_PRIMARY, COLOR_SUCCESS]

    my_posts_grid = ft.GridView(expand=False, runs_count=3, max_extent=110,
                                spacing=6, run_spacing=6, height=360)
    my_posts_status = ft.Text("", color=COLOR_TEXT_MUTED, size=12)
    my_posts_tab_state = {"active": "grid"}

    def get_my_posts():
        user_id = get_cached_user_id()
        if not user_id:
            return []
        try:
            resp = supabase.table("posts").select("*").eq("user_id", user_id).order("created_at", desc=True).limit(30).execute()
            return resp.data or []
        except Exception as ex:
            print(f"get_my_posts error: {ex}")
            return []

    # --- EDIT POST DIALOG (from the 3-dot menu on a post tile) ---
    def open_edit_post_dialog(post):
        edit_field = ft.TextField(
            value=post.get("content") or "", label="Post text", multiline=True, max_lines=5,
            width=DIALOG_WIDTH, color="white", border_color=COLOR_PRIMARY
        )
        status = ft.Text("", size=11)

        def close_dlg(d):
            d.open = False
            page.update()

        def save_edit(e):
            new_text = (edit_field.value or "").strip()
            try:
                supabase.table("posts").update({"content": new_text}).eq("id", post["id"]).execute()
                post["content"] = new_text
                status.value = "Post updated! ✅"
                status.color = COLOR_SUCCESS
                page.update()
                render_my_posts_grid()
                render_public_feed()
            except Exception as ex:
                status.value = f"Couldn't update: {str(ex)}"
                status.color = COLOR_DANGER
                page.update()

        dlg = ft.AlertDialog(
            title=ft.Text("Edit Post", color="white", size=16),
            bgcolor=COLOR_CARD,
            content=ft.Column([edit_field, status], tight=True, spacing=10, width=DIALOG_WIDTH),
            actions=[
                ft.TextButton("Save", on_click=save_edit),
                ft.TextButton("Close", on_click=lambda ev: close_dlg(dlg))
            ]
        )
        page.overlay.append(dlg)
        dlg.open = True
        page.update()

    def handle_delete_from_grid(post):
        handle_delete_post(post)  # cleans up media + deletes row + refreshes public feed
        render_my_posts_grid()
        stats = get_my_stats()
        profile_stat_posts.value = format_count(stats["posts"])
        profile_stat_likes.value = format_count(stats["likes"])
        page.update()

    def get_share_count(post):
        """Best-effort share count. UniVibe doesn't have a dedicated shares
        table — reposts (see handle_repost) reuse the original media_url,
        so counting other posts pointing at the same media file is the
        closest real signal we have. Text-only posts fall back to matching
        on a slice of the original content."""
        try:
            post_id = post.get("id")
            media_url = post.get("media_url")
            if media_url:
                resp = supabase.table("posts").select("id", count="exact") \
                    .eq("media_url", media_url).neq("id", post_id).execute()
                return resp.count or 0
            content_snip = (post.get("content") or "")[:40].strip()
            if not content_snip:
                return 0
            resp = supabase.table("posts").select("id", count="exact") \
                .ilike("content", f"%{content_snip}%").neq("id", post_id).execute()
            return resp.count or 0
        except Exception as ex:
            print(f"get_share_count error: {ex}")
            return 0

    # --- IMMERSIVE FULL-SCREEN POST VIEWER (TikTok-style) ---
    post_viewer_state = {"post": None}
    post_viewer_username = ft.Text("", weight=ft.FontWeight.BOLD, color=COLOR_PRIMARY, size=15)
    post_viewer_media_area = ft.Container(alignment=ft.Alignment.CENTER)
    post_viewer_content_text = ft.Text("", color=COLOR_TEXT_BODY, size=14)
    post_viewer_like_btn = ft.IconButton(icon=ft.Icons.FAVORITE_ROUNDED, icon_color=COLOR_TEXT_FAINT, icon_size=26)
    post_viewer_like_count = ft.Text("0", color="white", size=13)
    post_viewer_comment_count = ft.Text("0 comments", color=COLOR_TEXT_MUTED, size=12)
    post_viewer_share_count = ft.Text("0 shares", color=COLOR_TEXT_MUTED, size=12)
    post_viewer_comments_col = ft.Column(spacing=6, scroll=ft.ScrollMode.AUTO, height=160)
    post_viewer_comment_input = ft.TextField(hint_text="Add a comment...", expand=True, dense=True,
                                             color="white", border_color=COLOR_BORDER, content_padding=10)

    def close_post_viewer(e=None):
        post_viewer_overlay.visible = False
        page.update()

    def load_post_viewer_comments(post_id):
        post_viewer_comments_col.controls.clear()
        try:
            resp = supabase.rpc("get_post_comments", {"p_post_id": post_id}).execute()
            comments = resp.data or []
            post_viewer_comment_count.value = f"{len(comments)} comment{'s' if len(comments) != 1 else ''}"
            for c in comments:
                post_viewer_comments_col.controls.append(
                    ft.Container(
                        content=ft.Column([
                            ft.Text(c["username"], weight=ft.FontWeight.BOLD, color=COLOR_PRIMARY, size=12),
                            ft.Text(c["content"], color=COLOR_TEXT_BODY, size=13)
                        ], spacing=2),
                        padding=SPACE_MD, bgcolor=COLOR_CARD, border_radius=RADIUS_SM
                    )
                )
            if not comments:
                post_viewer_comments_col.controls.append(
                    ft.Text("No comments yet. Be first!", color=COLOR_TEXT_MUTED, size=12)
                )
        except Exception as ex:
            print(f"post viewer comments error: {ex}")
        page.update()

    def submit_post_viewer_comment(e):
        post = post_viewer_state["post"]
        if not post:
            return
        content = (post_viewer_comment_input.value or "").strip()
        if not content:
            return
        try:
            supabase.rpc("add_post_comment", {
                "p_post_id": post["id"],
                "p_user_id": get_cached_user_id(),
                "p_username": user_cache.get("username", "Unknown"),
                "p_content": content
            }).execute()
            post_viewer_comment_input.value = ""
            load_post_viewer_comments(post["id"])
            create_notification(post.get("user_id"), "comment",
                                f"{user_cache.get('username','Someone')} commented on your post", post["id"])
        except Exception as ex:
            print(f"post viewer submit comment error: {ex}")

    def toggle_post_viewer_like(e):
        post = post_viewer_state["post"]
        if not post:
            return
        handle_toggle_like(post["id"], post_viewer_like_btn, post_viewer_like_count, post.get("user_id"))

    post_viewer_like_btn.on_click = toggle_post_viewer_like

    def open_post_viewer(post):
        post_viewer_state["post"] = post
        is_anon = post.get("is_anonymous", False)
        post_viewer_username.value = "Anonymous Ghost \U0001F47B" if is_anon else f"@{post.get('username','Unknown')}"
        post_viewer_content_text.value = post.get("content") or ""

        media_url = post.get("media_url")
        media_type = post.get("media_type")
        if media_url and media_type == "image":
            post_viewer_media_area.content = ft.Image(
                src=media_url, width=340, height=380, fit=ft.BoxFit.CONTAIN, border_radius=RADIUS_MD
            )
        elif media_url and media_type == "video":
            viewer_video_container = ft.Container(
                content=ft.Column([
                    ft.Icon(ft.Icons.PLAY_CIRCLE_ROUNDED, color="white", size=64),
                    ft.Text("Tap to play video", color="white", size=12)
                ], alignment=ft.MainAxisAlignment.CENTER, horizontal_alignment=ft.CrossAxisAlignment.CENTER),
                width=340, height=380, bgcolor=COLOR_CARD, border_radius=RADIUS_MD,
                alignment=ft.Alignment.CENTER,
            )
            viewer_video_container.on_click = make_play_video_handler(
                viewer_video_container, media_url, 340, 380
            )
            post_viewer_media_area.content = viewer_video_container
        else:
            post_viewer_media_area.content = ft.Container(
                content=ft.Text(post.get("content") or "", color="white", size=18,
                                weight=ft.FontWeight.BOLD, text_align=ft.TextAlign.CENTER),
                width=340, height=380, bgcolor=COLOR_PRIMARY, border_radius=RADIUS_MD,
                alignment=ft.Alignment.CENTER, padding=20
            )

        post_id = post.get("id")
        likes_map = get_likes_map([post_id] if post_id else [])
        like_info = likes_map.get(post_id, {})
        post_viewer_like_btn.icon_color = COLOR_DANGER if like_info.get("user_liked") else COLOR_TEXT_FAINT
        post_viewer_like_count.value = str(like_info.get("like_count", 0))

        load_post_viewer_comments(post_id)

        share_count = get_share_count(post)
        post_viewer_share_count.value = f"{share_count} share{'s' if share_count != 1 else ''}"

        post_viewer_overlay.visible = True
        page.update()

    post_viewer_overlay = ft.Container(
        visible=False,
        bgcolor=COLOR_BG,
        padding=SPACE_LG,
        width=400,
        height=780,
        content=ft.Column([
            ft.Row([
                ft.IconButton(icon=ft.Icons.CLOSE_ROUNDED, icon_color="white", on_click=close_post_viewer),
                post_viewer_username,
            ], alignment=ft.MainAxisAlignment.START),
            post_viewer_media_area,
            post_viewer_content_text,
            ft.Row([
                post_viewer_like_btn, post_viewer_like_count,
                ft.Icon(ft.Icons.CHAT_BUBBLE_OUTLINE_ROUNDED, color=COLOR_TEXT_FAINT, size=20),
                post_viewer_comment_count,
                ft.IconButton(
                    icon=ft.Icons.SHARE_ROUNDED, icon_color=COLOR_TEXT_FAINT, icon_size=22, tooltip="Share",
                    on_click=lambda e: open_share_dialog(post_viewer_state["post"]) if post_viewer_state["post"] else None
                ),
                post_viewer_share_count
            ], spacing=6),
            ft.Divider(color=COLOR_BORDER),
            ft.Text("Comments", color="white", weight=ft.FontWeight.BOLD, size=13),
            post_viewer_comments_col,
            ft.Row([
                post_viewer_comment_input,
                ft.IconButton(icon=ft.Icons.SEND_ROUNDED, icon_color=COLOR_PRIMARY, on_click=submit_post_viewer_comment)
            ])
        ], spacing=10, scroll=ft.ScrollMode.AUTO),
    )
    page.overlay.append(post_viewer_overlay)

    def render_my_posts_grid():
        my_posts_grid.controls.clear()

        if my_posts_tab_state["active"] == "saved":
            my_posts_status.value = "Saved posts aren't available yet."
            my_posts_status.color = COLOR_TEXT_MUTED
            page.update()
            return

        posts = get_my_posts()
        if my_posts_tab_state["active"] == "reels":
            posts = [p for p in posts if p.get("media_type") == "video"]

        my_posts_status.value = "" if posts else "No posts yet."
        my_posts_status.color = COLOR_TEXT_MUTED

        post_ids = [p["id"] for p in posts if p.get("id")]
        likes_map = get_likes_map(post_ids)

        for idx, p in enumerate(posts):
            like_count = likes_map.get(p.get("id"), {}).get("like_count", 0)
            media_url = p.get("media_url")
            media_type = p.get("media_type")

            if media_url and media_type == "image":
                tile_content = ft.Image(src=media_url, fit=ft.BoxFit.COVER, width=110, height=110)
                tile_bg = COLOR_CARD
            elif media_url and media_type == "video":
                tile_content = ft.Container(
                    content=ft.Icon(ft.Icons.PLAY_CIRCLE_ROUNDED, color="white", size=32),
                    alignment=ft.Alignment.CENTER
                )
                tile_bg = COLOR_CARD
            else:
                accent = CARD_ACCENT_COLORS[idx % len(CARD_ACCENT_COLORS)]
                preview_text = (p.get("content") or "")[:60]
                text_color = "#1e1b12" if accent == COLOR_WARNING else "white"
                tile_content = ft.Container(
                    content=ft.Text(preview_text, color=text_color, weight=ft.FontWeight.BOLD,
                                    size=12, max_lines=3),
                    padding=8, alignment=ft.Alignment.CENTER
                )
                tile_bg = accent

            count_badge = ft.Row([
                ft.Icon(ft.Icons.PLAY_ARROW_ROUNDED, color="white", size=12),
                ft.Text(str(like_count), color="white", size=11)
            ], spacing=2)

            def make_edit_handler(post=p):
                def handler(e):
                    open_edit_post_dialog(post)
                return handler

            def make_delete_handler(post=p):
                def handler(e):
                    handle_delete_from_grid(post)
                return handler

            def make_view_handler(post=p):
                def handler(e):
                    open_post_viewer(post)
                return handler

            post_menu_btn = ft.PopupMenuButton(
                icon=ft.Icons.MORE_VERT_ROUNDED,
                icon_color="white",
                icon_size=16,
                tooltip="Post options",
                items=[
                    ft.PopupMenuItem(
                        content=ft.Row([
                            ft.Icon(ft.Icons.EDIT_ROUNDED, size=16, color=COLOR_PRIMARY),
                            ft.Text("Edit", color="white", size=13)
                        ], spacing=8),
                        on_click=make_edit_handler()
                    ),
                    ft.PopupMenuItem(
                        content=ft.Row([
                            ft.Icon(ft.Icons.DELETE_OUTLINE_ROUNDED, size=16, color=COLOR_DANGER),
                            ft.Text("Delete", color="white", size=13)
                        ], spacing=8),
                        on_click=make_delete_handler()
                    ),
                ]
            )

            my_posts_grid.controls.append(
                ft.Container(
                    content=ft.Stack([
                        ft.Container(content=tile_content, width=110, height=110, bgcolor=tile_bg,
                                    border_radius=RADIUS_SM, alignment=ft.Alignment.CENTER),
                        ft.Container(content=post_menu_btn, alignment=ft.Alignment.TOP_RIGHT),
                        ft.Container(content=count_badge, alignment=ft.Alignment.BOTTOM_LEFT, padding=6)
                    ], width=110, height=110),
                    width=110, height=110,
                    on_click=make_view_handler()
                )
            )
        page.update()

    def switch_posts_tab(tab_key):
        def handler(e):
            my_posts_tab_state["active"] = tab_key
            for key, btn in my_posts_tab_buttons.items():
                btn.icon_color = COLOR_PRIMARY if key == tab_key else COLOR_TEXT_MUTED
            render_my_posts_grid()
            page.update()
        return handler

    my_posts_tab_buttons = {
        "grid": ft.IconButton(icon=ft.Icons.GRID_VIEW_ROUNDED, icon_color=COLOR_PRIMARY, icon_size=20, tooltip="Posts"),
        "reels": ft.IconButton(icon=ft.Icons.SMART_DISPLAY_OUTLINED, icon_color=COLOR_TEXT_MUTED, icon_size=20, tooltip="Videos"),
        "saved": ft.IconButton(icon=ft.Icons.BOOKMARK_BORDER_ROUNDED, icon_color=COLOR_TEXT_MUTED, icon_size=20, tooltip="Saved"),
    }
    my_posts_tab_buttons["grid"].on_click = switch_posts_tab("grid")
    my_posts_tab_buttons["reels"].on_click = switch_posts_tab("reels")
    my_posts_tab_buttons["saved"].on_click = switch_posts_tab("saved")

    my_posts_section = ft.Column([
        ft.Row([
            ft.Text("My Posts", size=16, weight=ft.FontWeight.BOLD, color="white"),
            ft.TextButton(content=ft.Text("See All", color=COLOR_PRIMARY, size=12), on_click=nav_to_feed)
        ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN, width=300),
        ft.Row(
            [my_posts_tab_buttons["grid"], my_posts_tab_buttons["reels"], my_posts_tab_buttons["saved"]],
            alignment=ft.MainAxisAlignment.CENTER, spacing=30
        ),
        ft.Divider(height=1, color=COLOR_BORDER),
        my_posts_status,
        my_posts_grid
    ], spacing=10, width=340, horizontal_alignment=ft.CrossAxisAlignment.CENTER)

    # Guards load_own_profile() against overlapping calls: if the user taps
    # into Profile again before a slow fetch finishes, the older call's
    # results must never land on screen after the newer call's results —
    # each call checks this token before writing to any shared control.
    profile_load_state = {"token": 0}

    def load_own_profile():
        user_id = get_cached_user_id()
        if not user_id:
            return

        profile_load_state["token"] += 1
        my_token = profile_load_state["token"]

        def superseded():
            return profile_load_state["token"] != my_token

        try:
            resp = supabase.table("profiles").select("*").eq("user_id", user_id).execute()
            if superseded():
                return  # a newer load_own_profile() call has already started
            if not resp.data:
                return
            p = resp.data[0]
            profile_username_label.value = f"@{p.get('username', '')}"
            profile_bio.value = p.get("bio") or ""
            profile_school.value = p.get("school") or ""
            avatar = p.get("avatar_url")
            if avatar:
                profile_avatar_img.src = avatar
            else:
                uname = p.get("username", "U")
                profile_avatar_img.src = f"https://ui-avatars.com/api/?background=6366f1&color=fff&size=80&name={uname}"
            set_dd_value(dept_dd, p.get("department"))
            set_dd_value(country_dd, p.get("country"))
            saved_state = p.get("state")
            set_dd_value(state_dd, saved_state)
            # Populate LGA options for the saved state, then set the saved LGA
            lga_dd.options = [ft.dropdown.Option(o) for o in NIGERIA_LGAS_BY_STATE.get(saved_state, [])]
            set_dd_value(lga_dd, p.get("local_government"))

            # Stats row (Posts / Followers / Following / Total Likes).
            # format_count() renders None as "—", never as a false "0", so
            # a failed fetch here is visibly "unknown" rather than looking
            # like you actually have zero friends.
            stats = get_my_stats()
            if superseded():
                return
            profile_stat_posts.value = format_count(stats["posts"])
            profile_stat_followers.value = format_count(stats["followers"])
            profile_stat_following.value = format_count(stats["following"])
            profile_stat_likes.value = format_count(stats["likes"])
            page.update()  # push fields + stats now, independent of the grid below

            # My Posts grid (below the form fields)
            my_posts_tab_state["active"] = "grid"
            for key, btn in my_posts_tab_buttons.items():
                btn.icon_color = COLOR_PRIMARY if key == "grid" else COLOR_TEXT_MUTED
            try:
                if not superseded():
                    render_my_posts_grid()
            except Exception as grid_ex:
                print(f"Error rendering My Posts grid: {grid_ex}")
                my_posts_status.value = "Couldn't load your posts — try again."
                my_posts_status.color = COLOR_DANGER

            if not superseded():
                page.update()
        except Exception as ex:
            print(f"Error loading profile: {ex}")

    def compress_image_for_upload(file_bytes, max_dimension=1080, quality=80):
        """Shrinks large phone photos before upload. Big uncompressed camera
        photos (8-15MB) are the usual cause of connection-drop upload errors.
        Takes raw bytes directly — works identically on web and desktop."""
        try:
            from PIL import Image
            import io
            img = Image.open(io.BytesIO(file_bytes))
            if img.mode in ("RGBA", "P"):
                img = img.convert("RGB")
            img.thumbnail((max_dimension, max_dimension))
            buffer = io.BytesIO()
            img.save(buffer, format="JPEG", quality=quality, optimize=True)
            return buffer.getvalue(), "image/jpeg"
        except ImportError:
            print("Pillow not installed — uploading original file uncompressed. Run: pip install Pillow")
            return file_bytes, "application/octet-stream"
        except Exception as ex:
            print(f"Compression failed, using original file: {ex}")
            return file_bytes, "application/octet-stream"

    def upload_with_retry(bucket, storage_path, file_bytes, content_type, max_retries=2):
        """Retries an upload up to 2 extra times if the connection drops mid-transfer."""
        last_error = None
        for attempt in range(max_retries + 1):
            try:
                supabase.storage.from_(bucket).upload(storage_path, file_bytes, {"content-type": content_type})
                return
            except Exception as ex:
                last_error = ex
                print(f"Upload attempt {attempt + 1} failed: {ex}")
        raise last_error

    async def handle_upload_avatar(e):
        files = await ft.FilePicker().pick_files(
            allow_multiple=False,
            file_type=ft.FilePickerFileType.CUSTOM,
            allowed_extensions=["jpg", "jpeg", "png", "gif", "webp"],
            with_data=True
        )
        if not files:
            return
        f = files[0]
        if not f.bytes:
            profile_status_text.value = "Couldn't read that file — try again."
            profile_status_text.color = COLOR_DANGER
            page.update()
            return
        try:
            user_id = get_cached_user_id()
            file_bytes, content_type = compress_image_for_upload(f.bytes)
            storage_path = f"{user_id}/avatar.jpg"
            # Remove old avatar first (ignore errors)
            try:
                supabase.storage.from_(AVATARS_BUCKET).remove([storage_path])
            except Exception:
                pass
            upload_with_retry(AVATARS_BUCKET, storage_path, file_bytes, content_type)
            avatar_url = supabase.storage.from_(AVATARS_BUCKET).get_public_url(storage_path)
            supabase.table("profiles").update({"avatar_url": avatar_url}).eq("user_id", user_id).execute()
            profile_avatar_img.src = avatar_url
            profile_status_text.value = "Profile picture updated! ✅"
            profile_status_text.color = COLOR_SUCCESS
            page.update()
        except Exception as ex:
            profile_status_text.value = f"Avatar upload failed: {str(ex)}"
            profile_status_text.color = COLOR_DANGER
            page.update()

    def handle_save_profile(e):
        user_id = get_cached_user_id()
        if not user_id:
            return
        updates = {
            "bio": profile_bio.value or None,
            "school": profile_school.value.strip() or None,
            "department": get_dd_value(dept_dd),
            "country": get_dd_value(country_dd),
            "state": get_dd_value(state_dd),
            "local_government": get_dd_value(lga_dd),
        }
        try:
            supabase.table("profiles").update(updates).eq("user_id", user_id).execute()
            profile_status_text.value = "Profile saved! ✅"
            profile_status_text.color = COLOR_SUCCESS
            page.update()
        except Exception as ex:
            profile_status_text.value = f"Save failed: {str(ex)}"
            profile_status_text.color = COLOR_DANGER
            page.update()

    profile_edit_content = ft.Column([
        # --- Header: avatar + username + change photo (unchanged position) ---
        ft.Row([
            profile_avatar_img,
            ft.Column([
                profile_username_label,
                ft.ElevatedButton(
                    content=ft.Text("Change Photo", size=11, color="white"),
                    bgcolor=COLOR_PRIMARY, on_click=handle_upload_avatar, height=32
                )
            ], spacing=6)
        ], alignment=ft.MainAxisAlignment.CENTER, spacing=16),
        # --- Stats row: Posts / Followers / Following / Total Likes ---
        profile_stats_row,
        # --- Input / dropdown fields (unchanged order) ---
        profile_bio,
        profile_school,
        dept_dd,
        country_dd,
        state_dd,
        lga_dd,
        # --- My Posts: tab nav + content grid, directly below the fields ---
        my_posts_section,
        # --- Save button, at the very bottom beneath the post grid ---
        ft.ElevatedButton(
            content=ft.Text("Save Profile", color="white"),
            bgcolor=COLOR_PRIMARY, width=300, on_click=handle_save_profile
        ),
        profile_status_text
    ], spacing=12, horizontal_alignment=ft.CrossAxisAlignment.CENTER)

    # --- VIEW OTHER USER'S PROFILE ---
    view_profile_avatar = ft.Image(
        src="https://ui-avatars.com/api/?background=6366f1&color=fff&size=80&name=U",
        width=80, height=80, fit=ft.BoxFit.COVER, border_radius=40
    )
    view_profile_username = ft.Text("", size=18, weight=ft.FontWeight.BOLD, color=COLOR_PRIMARY)
    view_profile_bio      = ft.Text("", color=COLOR_TEXT_BODY, size=13, italic=True)
    view_profile_school   = ft.Text("", color=COLOR_TEXT_BODY, size=13)
    view_profile_dept     = ft.Text("", color=COLOR_TEXT_BODY, size=13)
    view_profile_country  = ft.Text("", color=COLOR_TEXT_BODY, size=13)
    view_profile_state    = ft.Text("", color=COLOR_TEXT_BODY, size=13)
    view_profile_lga      = ft.Text("", color=COLOR_TEXT_BODY, size=13)

    viewed_profile_state = {"user_id": None, "username": None}

    def load_other_profile(username):
        try:
            resp = supabase.table("profiles").select("*").eq("username", username).execute()
            if not resp.data:
                return
            p = resp.data[0]
            uname = p.get("username", "U")
            viewed_profile_state["user_id"] = p.get("user_id")
            viewed_profile_state["username"] = uname
            view_profile_username.value = f"@{uname}"
            avatar = p.get("avatar_url")
            view_profile_avatar.src = avatar if avatar else f"https://ui-avatars.com/api/?background=6366f1&color=fff&size=80&name={uname}"
            view_profile_bio.value     = p.get("bio") or ""
            view_profile_school.value  = f"\U0001F3EB  {p['school']}"  if p.get("school")           else ""
            view_profile_dept.value    = f"\U0001F4DA  {p['department']}" if p.get("department")     else ""
            view_profile_country.value = f"\U0001F30D  {p['country']}"  if p.get("country")          else ""
            view_profile_state.value   = f"\U0001F4CD  {p['state']}"    if p.get("state")            else ""
            view_profile_lga.value     = f"\U0001F3D8  {p['local_government']}" if p.get("local_government") else ""
            profile_view_status.value = ""
            panel_view_profile.visible = True
            panel_settings.visible     = False
            panel_home_feed.visible    = False
            panel_whisper_wall.visible = False
            panel_messages.visible     = False
            panel_people.visible       = False
            panel_reels.visible        = False
            panel_notifications.visible = False
            page.update()
            refresh_friend_button()
        except Exception as ex:
            print(f"Error loading other profile: {ex}")

    def close_profile_view(e):
        panel_view_profile.visible = False
        set_panel_visibility(feed=True)
        render_public_feed()

    # --- ADD FRIEND / CONNECTION STATUS BUTTON ---
    friend_btn_text = ft.Text("Add Friend", color="white", size=13)
    friend_btn_icon = ft.Icon(ft.Icons.PERSON_ADD_ALT_1_ROUNDED, color="white", size=16)
    friend_action_state = {"status": None, "request_id": None, "is_requester": None}

    def refresh_friend_button():
        target_id = viewed_profile_state["user_id"]
        my_id = get_cached_user_id()
        if not target_id or not my_id or target_id == my_id:
            friend_button.visible = False
            page.update()
            return

        friend_button.visible = True
        status, request_id, is_requester = get_connection_status(target_id)
        friend_action_state["status"] = status
        friend_action_state["request_id"] = request_id
        friend_action_state["is_requester"] = is_requester

        if status == "accepted":
            friend_btn_icon.name = ft.Icons.CHECK_CIRCLE_ROUNDED
            friend_btn_text.value = "Connected"
            friend_button.bgcolor = COLOR_BORDER
            friend_button.disabled = True
        elif status == "pending" and is_requester:
            friend_btn_icon.name = ft.Icons.HOURGLASS_TOP_ROUNDED
            friend_btn_text.value = "Pending"
            friend_button.bgcolor = COLOR_BORDER
            friend_button.disabled = True
        elif status == "pending" and not is_requester:
            friend_btn_icon.name = ft.Icons.PERSON_ADD_ALT_1_ROUNDED
            friend_btn_text.value = "Respond to Request"
            friend_button.bgcolor = COLOR_WARNING
            friend_button.disabled = False
        else:
            # None, or 'declined' (declined is treated as re-requestable)
            friend_btn_icon.name = ft.Icons.PERSON_ADD_ALT_1_ROUNDED
            friend_btn_text.value = "Add Friend"
            friend_button.bgcolor = COLOR_PRIMARY
            friend_button.disabled = False
        page.update()

    def open_respond_to_request_dialog():
        target_name = viewed_profile_state["username"]

        def handle_result(accept, error):
            if error:
                profile_view_status.value = error
                profile_view_status.color = COLOR_DANGER
            else:
                profile_view_status.value = (
                    f"You're now connected with @{target_name}!" if accept
                    else f"Declined @{target_name}'s request."
                )
                profile_view_status.color = COLOR_SUCCESS if accept else COLOR_TEXT_MUTED
            refresh_friend_button()
            page.update()

        open_respond_dialog(friend_action_state["request_id"], target_name, on_responded=handle_result)

    def handle_friend_button_click(e):
        status = friend_action_state["status"]
        is_requester = friend_action_state["is_requester"]

        if status == "pending" and not is_requester:
            open_respond_to_request_dialog()
            return

        if status in ("accepted",) or (status == "pending" and is_requester):
            return  # button is disabled in these states already

        target_id = viewed_profile_state["user_id"]
        target_name = viewed_profile_state["username"]
        result, error = send_connection_request(target_id)
        if error:
            profile_view_status.value = error
            profile_view_status.color = COLOR_DANGER
        elif result == "accepted":
            profile_view_status.value = f"You're now connected with @{target_name}!"
            profile_view_status.color = COLOR_SUCCESS
        elif result == "already_connected":
            profile_view_status.value = f"You're already connected with @{target_name}."
            profile_view_status.color = COLOR_TEXT_MUTED
        else:
            profile_view_status.value = f"Request sent to @{target_name}."
            profile_view_status.color = COLOR_SUCCESS
        refresh_friend_button()
        page.update()

    friend_button = ft.ElevatedButton(
        content=ft.Row([friend_btn_icon, friend_btn_text], spacing=6,
                       alignment=ft.MainAxisAlignment.CENTER),
        bgcolor=COLOR_PRIMARY, width=280, on_click=handle_friend_button_click, visible=False
    )

    def handle_block_from_profile(e):
        target_id = viewed_profile_state["user_id"]
        target_name = viewed_profile_state["username"]
        if not target_id:
            return
        if block_user_action(target_id):
            profile_view_status.value = f"@{target_name} has been blocked."
            profile_view_status.color = COLOR_SUCCESS
        else:
            profile_view_status.value = "Couldn't block — try again."
            profile_view_status.color = COLOR_DANGER
        page.update()

    def open_report_user_dialog(e):
        reason_dd = ft.Dropdown(
            label="Reason", width=DIALOG_WIDTH, color="white",
            options=[ft.dropdown.Option(r) for r in REPORT_REASONS]
        )
        status = ft.Text("", size=11)

        def close_dlg(d):
            d.open = False
            page.update()

        def submit_report(ev):
            if not reason_dd.value:
                status.value = "Please choose a reason."
                status.color = COLOR_DANGER
                page.update()
                return
            if report_user_action(viewed_profile_state["user_id"], reason_dd.value):
                status.value = "Reported. Our team will review it."
                status.color = COLOR_SUCCESS
                page.update()
            else:
                status.value = "Couldn't submit report — try again."
                status.color = COLOR_DANGER
                page.update()

        dlg = ft.AlertDialog(
            title=ft.Text(f"Report @{viewed_profile_state['username']}", color="white", size=15),
            bgcolor=COLOR_CARD,
            content=ft.Column([reason_dd, status], tight=True, spacing=10),
            actions=[
                ft.TextButton("Submit", on_click=submit_report),
                ft.TextButton("Close", on_click=lambda ev: close_dlg(dlg))
            ]
        )
        page.overlay.append(dlg)
        dlg.open = True
        page.update()

    profile_view_status = ft.Text("", size=12)

    panel_view_profile = ft.Column([
        ft.Row([
            ft.IconButton(icon=ft.Icons.ARROW_BACK_ROUNDED, icon_color=COLOR_PRIMARY, on_click=close_profile_view),
            ft.Text("Profile", size=16, weight=ft.FontWeight.BOLD, color="white")
        ]),
        view_profile_avatar,
        view_profile_username,
        view_profile_bio,
        ft.Divider(color=COLOR_BORDER),
        view_profile_school,
        view_profile_dept,
        view_profile_country,
        view_profile_state,
        view_profile_lga,
        friend_button,
        ft.ElevatedButton(
            content=ft.Text("Send Message", color="white"),
            bgcolor=COLOR_SUCCESS, width=280,
            on_click=lambda e: handle_start_chat_from_profile()
        ),
        ft.Row([
            ft.TextButton(
                content=ft.Row([ft.Icon(ft.Icons.BLOCK_ROUNDED, color=COLOR_DANGER, size=16),
                                ft.Text("Block", color=COLOR_DANGER, size=12)], spacing=4),
                on_click=handle_block_from_profile
            ),
            ft.TextButton(
                content=ft.Row([ft.Icon(ft.Icons.FLAG_ROUNDED, color=COLOR_TEXT_MUTED, size=16),
                                ft.Text("Report", color=COLOR_TEXT_MUTED, size=12)], spacing=4),
                on_click=open_report_user_dialog
            ),
        ], alignment=ft.MainAxisAlignment.CENTER),
        profile_view_status
    ], visible=False, horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=10)

    def handle_start_chat_from_profile():
        uname = view_profile_username.value.lstrip("@")
        conv_id, error = get_or_create_conversation(uname)
        if error:
            return
        panel_view_profile.visible = False
        set_panel_visibility(chats=True)
        open_thread(conv_id, uname)

    panel_settings = ft.Column([
        ft.Text("My Profile", size=18, weight=ft.FontWeight.BOLD, color="white"),
        profile_edit_content
    ], visible=False, horizontal_alignment=ft.CrossAxisAlignment.CENTER)

    # ============================================================
    # --- AUTH: LOGIN / REGISTER (email + password, no OTP) ---
    # ============================================================
    input_login_email = ft.TextField(label="Email or Username", width=300, color="white")
    input_login_password = ft.TextField(label="Password", password=True, width=300, color="white")

    ui_message = ft.Text("", size=14)

    # --- STORAGE COMPATIBILITY SHIM ---
    # Different Flet versions expose persistent storage as either page.client_storage
    # (sync, older versions) or page.shared_preferences (async, newer versions).
    # These helpers detect which one exists on THIS install and use it, so the app
    # doesn't break across Flet upgrades/downgrades.
    async def storage_set(key, value):
        if hasattr(page, "shared_preferences"):
            await page.shared_preferences.set(key, value)
        else:
            page.client_storage.set(key, value)

    async def storage_get(key):
        if hasattr(page, "shared_preferences"):
            return await page.shared_preferences.get(key)
        else:
            return page.client_storage.get(key)

    async def storage_remove(key):
        if hasattr(page, "shared_preferences"):
            await page.shared_preferences.remove(key)
        else:
            page.client_storage.remove(key)

    async def save_session(session, user=None):
        # Persists the Supabase session so the user stays logged in after restart
        await storage_set("univibe_access_token", session.access_token)
        await storage_set("univibe_refresh_token", session.refresh_token)
        # Also store user_id and email directly so we never need get_user() on restore
        if user:
            await storage_set("univibe_user_id", user.id)
            await storage_set("univibe_user_email", user.email or "")

    async def clear_session():
        await storage_remove("univibe_access_token")
        await storage_remove("univibe_refresh_token")
        await storage_remove("univibe_user_id")
        await storage_remove("univibe_user_email")

    def show_dashboard():
        layout_auth_master.visible = False
        layout_dashboard_master.visible = True
        set_panel_visibility(feed=True)
        render_public_feed()
        highlight_nav("feed")
        refresh_notification_badge()
        page.update()

    def show_auth():
        layout_dashboard_master.visible = False
        layout_auth_master.visible = True
        reg_step1.visible = False
        reg_step2.visible = False
        reg_step3.visible = False
        layout_login_form.visible = True
        page.update()

    def switch_to_register(e):
        layout_login_form.visible = False
        reg_step1.visible = True
        reg_step2.visible = False
        reg_step3.visible = False
        ui_message.value = ""
        page.update()

    def switch_to_login(e):
        reg_step1.visible = False
        reg_step2.visible = False
        reg_step3.visible = False
        layout_login_form.visible = True
        ui_message.value = ""
        page.update()

    async def handle_login(e):
        if not input_login_email.value or not input_login_password.value:
            ui_message.value = "Please enter your email/username and password."
            ui_message.color = COLOR_DANGER
            page.update()
            return
        try:
            login_input = input_login_email.value.strip()
            if "@" in login_input:
                login_email = login_input
            else:
                # Treat as username — resolve to the account's email via profiles
                lookup = supabase.table("profiles").select("email").eq("username", login_input).execute()
                if not lookup.data or not lookup.data[0].get("email"):
                    ui_message.value = "No account found for that username."
                    ui_message.color = COLOR_DANGER
                    page.update()
                    return
                login_email = lookup.data[0]["email"]

            result = supabase.auth.sign_in_with_password({
                "email": login_email,
                "password": input_login_password.value
            })
            cache_user(result.user, result.session.access_token)
            await save_session(result.session, result.user)
            ui_message.value = ""
            show_dashboard()
        except Exception as ex:
            if "not confirmed" in str(ex).lower() or "confirm" in str(ex).lower():
                ui_message.value = "Please confirm your email first. Didn't get it? Tap Resend below."
            else:
                ui_message.value = f"Login failed: {str(ex)}"
            ui_message.color = COLOR_DANGER
            page.update()

    def handle_resend_confirmation(e):
        if not input_login_email.value or "@" not in input_login_email.value:
            ui_message.value = "Enter your email address above first, then tap Resend."
            ui_message.color = COLOR_DANGER
            page.update()
            return
        try:
            supabase.auth.resend({"type": "signup", "email": input_login_email.value})
            ui_message.value = "Confirmation email resent — check your inbox."
            ui_message.color = COLOR_SUCCESS
            page.update()
        except Exception as ex:
            ui_message.value = f"Couldn't resend: {str(ex)}"
            ui_message.color = COLOR_DANGER
            page.update()

    # ============================================================
    # --- 3-STEP OTP REGISTRATION ---
    # Step 1: username + email  -> sends 6-digit code (via Brevo)
    # Step 2: enter the code    -> verifies it, creates + confirms the account
    # Step 3: set a password    -> finalizes, logs the user in
    # ============================================================
    reg_state = {"username": None, "email": None}

    input_reg_username = ft.TextField(label="Username", width=300, color="white")
    input_reg_email = ft.TextField(label="Email Address", width=300, color="white")
    input_reg_otp = ft.TextField(label="6-Digit Code", width=300, color="white", max_length=6)
    input_reg_password = ft.TextField(label="Choose Password", password=True, width=300, color="white")
    input_reg_confirm = ft.TextField(label="Confirm Password", password=True, width=300, color="white")
    reg_step1_status = ft.Text("", size=12)
    reg_step2_status = ft.Text("", size=12)
    reg_step3_status = ft.Text("", size=12)

    TERMS_TEXT = """UNIVIBE — TERMS OF SERVICE & PRIVACY POLICY (Summary)

By creating an account, you agree to the following:

ELIGIBILITY
You must be at least 16 years old and provide accurate registration information.

ACCEPTABLE USE
You may not harass, bully, threaten, or impersonate others, post hate speech or illegal content, spam, or attempt to hack the platform.

ANONYMOUS POSTS (WHISPER WALL)
Anonymous posts hide your username from other users, but remain linked to your account internally so we can enforce these rules and investigate abuse reports. Anonymity applies to other users, not to the platform.

CONTENT
You own what you post. Posting it grants UniVibe permission to display it to other users. You're responsible for what you share.

MODERATION
We provide Block and Report tools. Violating these terms may result in content removal or account suspension.

WHAT WE COLLECT
Your email, username, password (encrypted), any profile details you choose to add, and the content you post/send.

HOW WE USE IT
To run the app's features (feed, chat, profiles), send account emails, and investigate reports. We do not sell your data.

WHO CAN SEE WHAT
Your username and public posts are visible to other users. Anonymous posts hide your name from other users only. Private messages are visible only to you and the recipient. Blocked users can't see or message you.

YOUR RIGHTS (Nigeria NDPR)
You can request a copy of your data, request corrections, or request full account deletion at any time by contacting the app developer.

CHANGES
We may update these terms; continued use of the app means you accept the changes."""

    def open_terms_dialog(e=None):
        def close_dlg(d):
            d.open = False
            page.update()

        dlg = ft.AlertDialog(
            title=ft.Text("Terms of Service & Privacy Policy", color="white", size=15),
            bgcolor=COLOR_CARD,
            content=ft.Column(
                [ft.Text(TERMS_TEXT, color=COLOR_TEXT_BODY, size=12)],
                scroll=ft.ScrollMode.AUTO, height=400, width=DIALOG_WIDTH
            ),
            actions=[ft.TextButton("Close", on_click=lambda ev: close_dlg(dlg))]
        )
        page.overlay.append(dlg)
        dlg.open = True
        page.update()

    agree_terms_checkbox = ft.Checkbox(label="", value=False)

    def handle_reg_step1_next(e):
        username = (input_reg_username.value or "").strip()
        email = (input_reg_email.value or "").strip()
        if not username or not email:
            reg_step1_status.value = "Please fill in both fields."
            reg_step1_status.color = COLOR_DANGER
            page.update()
            return
        if not agree_terms_checkbox.value:
            reg_step1_status.value = "You must agree to the Terms of Service & Privacy Policy to continue."
            reg_step1_status.color = COLOR_DANGER
            page.update()
            return
        try:
            # Sends the 6-digit code via your Brevo SMTP + email template.
            # should_create_user=True creates an unconfirmed, passwordless
            # account right now — it gets confirmed once the code is verified.
            supabase.auth.sign_in_with_otp({
                "email": email,
                "options": {"should_create_user": True}
            })
            reg_state["username"] = username
            reg_state["email"] = email
            reg_step1_status.value = ""
            reg_step1.visible = False
            reg_step2.visible = True
            reg_step2_status.value = f"Code sent to {email}. Check your inbox."
            reg_step2_status.color = COLOR_TEXT_MUTED
            page.update()
        except Exception as ex:
            reg_step1_status.value = f"Couldn't send code: {str(ex)}"
            reg_step1_status.color = COLOR_DANGER
            page.update()

    def handle_resend_reg_otp(e):
        if not reg_state["email"]:
            return
        try:
            supabase.auth.sign_in_with_otp({
                "email": reg_state["email"],
                "options": {"should_create_user": True}
            })
            reg_step2_status.value = "Code resent — check your inbox."
            reg_step2_status.color = COLOR_SUCCESS
            page.update()
        except Exception as ex:
            reg_step2_status.value = f"Couldn't resend: {str(ex)}"
            reg_step2_status.color = COLOR_DANGER
            page.update()

    def handle_verify_reg_otp(e):
        code = (input_reg_otp.value or "").strip()
        if not code:
            reg_step2_status.value = "Enter the 6-digit code."
            reg_step2_status.color = COLOR_DANGER
            page.update()
            return
        try:
            result = supabase.auth.verify_otp({
                "email": reg_state["email"],
                "token": code,
                "type": "email"
            })
            if not result.session or not result.user:
                reg_step2_status.value = "Verification failed — check the code and try again."
                reg_step2_status.color = COLOR_DANGER
                page.update()
                return

            # Explicitly hand the verified session to the auth client itself —
            # cache_user() only wires up postgrest.auth() for table/RPC calls,
            # it does NOT establish supabase.auth's own session. Without this,
            # supabase.auth.update_user() in step 3 fails with
            # "Auth session missing!" because the auth client has no session
            # to attach the password change to.
            supabase.auth.set_session(result.session.access_token, result.session.refresh_token)

            # Attach the JWT so the profile insert below passes RLS
            cache_user(result.user, result.session.access_token)
            reg_state["session"] = result.session  # keep for step 3, avoids relying on get_session()

            # Create the profile row now that the account is confirmed
            supabase.table("profiles").insert({
                "username": reg_state["username"],
                "location": "Not Specified Yet",
                "user_id": result.user.id,
                "email": reg_state["email"]
            }).execute()
            refresh_cached_username(result.user.id)

            reg_step2_status.value = ""
            reg_step2.visible = False
            reg_step3.visible = True
            page.update()
        except Exception as ex:
            msg = str(ex).lower()
            if "expired" in msg or "invalid" in msg:
                reg_step2_status.value = "That code is invalid or expired. Tap Resend for a new one."
            else:
                reg_step2_status.value = f"Verification failed: {str(ex)}"
            reg_step2_status.color = COLOR_DANGER
            page.update()

    async def handle_finalize_registration(e):
        if not input_reg_password.value or not input_reg_confirm.value:
            reg_step3_status.value = "Please fill in both password fields."
            reg_step3_status.color = COLOR_DANGER
            page.update()
            return
        if input_reg_password.value != input_reg_confirm.value:
            reg_step3_status.value = "Passwords do not match."
            reg_step3_status.color = COLOR_DANGER
            page.update()
            return
        try:
            # Re-assert the session right before the password update — belt and
            # braces in case anything cleared supabase.auth's in-memory session
            # between step 2 and step 3 (e.g. a hot-reload or a stray sign_out()
            # firing elsewhere in the app).
            if reg_state.get("session"):
                try:
                    supabase.auth.set_session(
                        reg_state["session"].access_token,
                        reg_state["session"].refresh_token
                    )
                except Exception as ex:
                    print(f"set_session before password update warning: {ex}")

            supabase.auth.update_user({"password": input_reg_password.value})
            # Use the session captured right after verify_otp() in step 2 —
            # more reliable than calling get_session() with an unverified shape
            if reg_state.get("session"):
                await save_session(reg_state["session"], None)
                await storage_set("univibe_user_id", user_cache["id"])
                await storage_set("univibe_user_email", user_cache["email"])
            reg_step3_status.value = ""
            show_dashboard()
        except Exception as ex:
            reg_step3_status.value = f"Couldn't set password: {str(ex)}"
            reg_step3_status.color = COLOR_DANGER
            page.update()

    reg_step1 = ft.Column([
        ft.Text("Create Account", size=18, weight=ft.FontWeight.BOLD, color="white"),
        input_reg_username,
        input_reg_email,
        ft.Row([
            agree_terms_checkbox,
            ft.Text("I agree to the", color=COLOR_TEXT_MUTED, size=12),
            ft.TextButton(content=ft.Text("Terms & Privacy Policy", color=COLOR_PRIMARY, size=12), on_click=open_terms_dialog)
        ], spacing=0),
        ft.ElevatedButton(content=ft.Text("Next", color="white"), on_click=handle_reg_step1_next, width=300, bgcolor=COLOR_SUCCESS),
        reg_step1_status,
        ft.TextButton(content=ft.Text("Already have an account? Log in", color=COLOR_TEXT_MUTED), on_click=switch_to_login)
    ], visible=False, horizontal_alignment=ft.CrossAxisAlignment.CENTER)

    reg_step2 = ft.Column([
        ft.Text("Verify Your Email", size=18, weight=ft.FontWeight.BOLD, color="white"),
        input_reg_otp,
        ft.ElevatedButton(content=ft.Text("Next", color="white"), on_click=handle_verify_reg_otp, width=300, bgcolor=COLOR_SUCCESS),
        reg_step2_status,
        ft.TextButton(content=ft.Text("Resend code", color=COLOR_TEXT_MUTED, size=12), on_click=handle_resend_reg_otp)
    ], visible=False, horizontal_alignment=ft.CrossAxisAlignment.CENTER)

    reg_step3 = ft.Column([
        ft.Text("Set Your Password", size=18, weight=ft.FontWeight.BOLD, color="white"),
        input_reg_password,
        input_reg_confirm,
        ft.ElevatedButton(content=ft.Text("Create Account", color="white"), on_click=handle_finalize_registration, width=300, bgcolor=COLOR_SUCCESS),
        reg_step3_status
    ], visible=False, horizontal_alignment=ft.CrossAxisAlignment.CENTER)

    layout_login_form = ft.Column([
        input_login_email,
        input_login_password,
        ft.ElevatedButton(content=ft.Text("Log In", color="white"), on_click=handle_login, width=300, bgcolor=COLOR_PRIMARY),
        ft.TextButton(content=ft.Text("New here? Create an account", color=COLOR_TEXT_MUTED), on_click=switch_to_register),
        ft.TextButton(content=ft.Text("Resend confirmation email", color=COLOR_TEXT_MUTED, size=12), on_click=handle_resend_confirmation)
    ], horizontal_alignment=ft.CrossAxisAlignment.CENTER)

    layout_auth_master = ft.Column([
        ft.Text("UniVibe", size=36, weight=ft.FontWeight.BOLD, color=COLOR_PRIMARY),
        layout_login_form,
        reg_step1,
        reg_step2,
        reg_step3,
        ui_message
    ], horizontal_alignment=ft.CrossAxisAlignment.CENTER)

    layout_dashboard_master = ft.Column([
        custom_nav_bar,
        panel_home_feed,
        panel_whisper_wall,
        panel_messages,
        panel_people,
        panel_reels,
        panel_notifications,
        panel_settings,
        panel_view_profile
    ], visible=False, horizontal_alignment="center")

    async def try_restore_session():
        try:
            access_token  = await storage_get("univibe_access_token")
            refresh_token = await storage_get("univibe_refresh_token")
            user_id       = await storage_get("univibe_user_id")
            user_email    = await storage_get("univibe_user_email")

            if access_token and refresh_token and user_id:
                # Restore the Supabase auth session — same as before
                try:
                    supabase.auth.set_session(access_token, refresh_token)
                    supabase.postgrest.auth(access_token)
                except Exception as ex:
                    print(f"set_session warning: {ex}")

                # Validate the restored token with one real query before
                # committing to it. A stored access_token can be expired
                # if the app was closed for a while (Supabase JWTs last
                # ~1 hour) — sending an expired token to a table that now
                # has RLS enforced comes back as "JWT expired" (PGRST303).
                # If that happens here, clear the dead session and drop
                # back to login instead of continuing into a dashboard
                # where every request would fail the same way.
                username_check = None
                try:
                    username_check = supabase.table("profiles").select("username").eq("user_id", user_id).execute()
                except Exception as ex:
                    msg = str(ex).lower()
                    if "jwt" in msg or "expired" in msg or "pgrst303" in msg:
                        print(f"Stored session is no longer valid — clearing it: {ex}")
                        await clear_session()
                        cache_user(None)
                        return False
                    # Some other (likely transient/network) error — fall
                    # through and let the app proceed; individual screens
                    # already handle their own fetch failures gracefully.

                # Rebuild the user cache directly from stored values —
                # never call get_user() here, it fails on the sync client
                user_cache["id"]           = user_id
                user_cache["email"]        = user_email
                user_cache["access_token"] = access_token
                if username_check and username_check.data and username_check.data[0].get("username"):
                    user_cache["username"] = username_check.data[0]["username"]
                else:
                    refresh_cached_username(user_id)  # Get the REAL username, not email prefix

                show_dashboard()
                return True
        except Exception as ex:
            print(f"Session restore failed: {ex}")
            await clear_session()
        return False

    page.add(layout_auth_master, layout_dashboard_master)

    if not await try_restore_session():
        show_auth()

if "--web" in sys.argv:
    # Run as: python main.py --web
    # Local testing: opens in a browser tab on port 8551.
    # Cloud hosting: uses the PORT the host assigns via environment variable,
    # and binds to 0.0.0.0 so external traffic can actually reach it.
    cloud_port = int(os.environ.get("PORT", 8551))
    ft.app(target=main, view=ft.AppView.WEB_BROWSER, host="0.0.0.0", port=cloud_port)
else:
    # Run as: python main.py
    ft.app(target=main)
