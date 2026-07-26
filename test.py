from supabase import create_client, Client  
import flet as ft  
import os  
import sys  
import uuid  
import mimetypes  
import asyncio  
import urllib.parse  
  
# --- LIVE DATABASE CONNECTION ---  
SUPABASE_URL = "https://vjvynztrznvlhxqatcsi.supabase.co"  
SUPABASE_KEY = "sb_publishable_CGotNkzRyXY-P7klDoCysw_hFoo-8rq"  
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)  
  
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
    page.title = "UniVibe - Master Console"  
    page.window_width = 400  
    page.window_height = 780  
    page.window_resizable = True  
    page.scroll = ft.ScrollMode.AUTO  
    page.horizontal_alignment = ft.CrossAxisAlignment.CENTER  
    page.bgcolor = "#0f172a"  
  
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
            now_liked = current_color != "#f43f5e"  
            like_btn.icon_color = "#f43f5e" if now_liked else "#64748b"  
            page.update()  
            if now_liked:  
                create_notification(post_owner_id, "like",  
                                    f"{user_cache.get('username','Someone')} liked your post", post_id)  
        except Exception as ex:  
            print(f"Like error: {ex}")  
  
    def open_comments_dialog(post_id, post_username, post_owner_id=None):  
        comment_input = ft.TextField(  
            hint_text="Write a comment…", width=260, dense=True, color="white"  
        )  
        comments_col = ft.Column(spacing=6, scroll=ft.ScrollMode.ALWAYS, height=200)  
        status = ft.Text("", size=11)  
  
        def load_comments():  
            comments_col.controls.clear()  
            try:  
                resp = supabase.rpc("get_post_comments", {"p_post_id": post_id}).execute()  
                for c in (resp.data or []):  
                    comments_col.controls.append(  
                        ft.Container(  
                            content=ft.Column([  
                                ft.Text(c["username"], weight=ft.FontWeight.BOLD,  
                                        color="#6366f1", size=12),  
                                ft.Text(c["content"], color="#e2e8f0", size=13)  
                            ], spacing=2),  
                            padding=8, bgcolor="#1e293b", border_radius=6  
                        )  
                    )  
                if not resp.data:  
                    comments_col.controls.append(  
                        ft.Text("No comments yet. Be first!", color="#94a3b8", size=12)  
                    )  
            except Exception as ex:  
                print(f"Comments load error: {ex}")  
            page.update()  
  
        def submit_comment(e):  
            content = (comment_input.value or "").strip()  
            if not content:  
                return  
            try:  
                supabase.rpc("add_post_comment", {  
                    "p_post_id": post_id,  
                    "p_user_id": get_cached_user_id(),  
                    "p_username": user_cache.get("username", "Unknown"),  
                    "p_content": content  
                }).execute()  
                comment_input.value = ""  
                load_comments()  
                create_notification(post_owner_id, "comment",  
                                    f"{user_cache.get('username','Someone')} commented on your post", post_id)  
            except Exception as ex:  
                status.value = f"Failed: {str(ex)}"  
                status.color = "red"  
                page.update()  
  
        dlg = ft.AlertDialog(  
            title=ft.Text(f"Comments on {post_username}'s post", color="white", size=14),  
            bgcolor="#0f172a",  
            content=ft.Column([  
                comments_col,  
                ft.Row([comment_input,  
                        ft.IconButton(icon=ft.Icons.SEND, icon_color="#6366f1",  
                                      on_click=submit_comment)]),  
                status  
            ], tight=True),  
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
                share_status.color = "red"  
                page.update()  
                return  
            conv_id, error = get_or_create_conversation(target)  
            if error:  
                share_status.value = error  
                share_status.color = "red"  
                page.update()  
                return  
            preview = (post.get("content") or "")[:100]  
            msg = f"\U0001F4E4 Shared a post: {preview}"  
            if post.get("media_url"):  
                msg += f"\n{post['media_url']}"  
            send_message(conv_id, msg)  
            share_status.value = "Shared! ✅"  
            share_status.color = "#10b981"  
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
            bgcolor="#1e293b",  
            content=ft.Column([  
                ft.Text("Share to a friend's chat:", color="#94a3b8", size=12),  
                ft.Row([share_username_input,  
                        ft.IconButton(icon=ft.Icons.SEND, icon_color="#6366f1", on_click=share_to_chat)]),  
                share_status,  
                ft.Divider(color="#334155"),  
                ft.ElevatedButton(  
                    content=ft.Row([ft.Icon(ft.Icons.SHARE, color="white", size=16),  
                                    ft.Text("Share via WhatsApp", color="white")], spacing=6),  
                    bgcolor="#25D366", on_click=share_whatsapp  
                )  
            ], tight=True, spacing=10),  
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
            label="Reason", width=260, color="white",  
            options=[ft.dropdown.Option(r) for r in REPORT_REASONS]  
        )  
        status = ft.Text("", size=11)  
  
        def close_dlg(d):  
            d.open = False  
            page.update()  
  
        def submit_report(e):  
            if not reason_dd.value:  
                status.value = "Please choose a reason."  
                status.color = "red"  
                page.update()  
                return  
            if report_post_action(post_id, reason_dd.value):  
                status.value = "Reported. Our team will review it."  
                status.color = "#10b981"  
                page.update()  
            else:  
                status.value = "Couldn't submit report — try again."  
                status.color = "red"  
                page.update()  
  
        dlg = ft.AlertDialog(  
            title=ft.Text("Report Post", color="white", size=16),  
            bgcolor="#1e293b",  
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
            name_color = "#f43f5e" if is_anon else "#6366f1"  
            name_icon = ft.Icons.SECURITY_OUTLINED if is_anon else ft.Icons.ACCOUNT_CIRCLE  
            icon_color = "#f43f5e" if is_anon else "#6366f1"  
  
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
                post_body.append(ft.Text(p["content"], color="#e2e8f0", size=14))  
  
            media_url = p.get("media_url")  
            if media_url and p.get("media_type") == "image":  
                post_body.append(  
                    ft.Image(src=media_url, width=300, height=180, fit=ft.BoxFit.COVER, border_radius=8)  
                )  
            elif media_url and p.get("media_type") == "video":  
                post_body.append(  
                    ft.Container(  
                        content=ft.Row([ft.Icon(ft.Icons.PLAY_CIRCLE_OUTLINE, color="white"),  
                                        ft.Text("Video attached — tap to view", color="white", size=12)]),  
                        padding=8, bgcolor="#334155", border_radius=6,  
                        on_click=lambda e, url=media_url: page.launch_url(url)  
                    )  
                )  
  
            # Like / Comment action bar  
            post_id = p.get("id")  
            like_info = likes_map.get(post_id, {})  
            like_count = like_info.get("like_count", 0)  
            user_liked = like_info.get("user_liked", False)  
            like_icon_color = "#f43f5e" if user_liked else "#64748b"  
  
            like_count_text = ft.Text(str(like_count), color="#94a3b8", size=12)  
            like_btn = ft.IconButton(  
                icon=ft.Icons.FAVORITE,  
                icon_color=like_icon_color,  
                icon_size=18  
            )  
            # Wire after creation so we can pass references  
            def make_like_handler(pid=post_id, lb=like_btn, lct=like_count_text, owner=p.get("user_id")):  
                like_btn.on_click = lambda e: handle_toggle_like(pid, lb, lct, owner)  
            make_like_handler()  
  
            comment_btn = ft.IconButton(  
                icon=ft.Icons.CHAT_BUBBLE_OUTLINE,  
                icon_color="#64748b", icon_size=18,  
                on_click=lambda e, pid=post_id, uname=p.get("username","Unknown"), owner=p.get("user_id"): open_comments_dialog(pid, uname, owner)  
            )  
  
            share_btn = ft.IconButton(  
                icon=ft.Icons.SHARE_OUTLINED,  
                icon_color="#64748b", icon_size=18,  
                tooltip="Share",  
                on_click=lambda e, post=p: open_share_dialog(post)  
            )  
  
            repost_btn = ft.IconButton(  
                icon=ft.Icons.REPEAT,  
                icon_color="#64748b", icon_size=18,  
                tooltip="Repost",  
                on_click=lambda e, post=p: handle_repost(post)  
            )  
  
            action_row_controls = [like_btn, like_count_text, comment_btn, share_btn, repost_btn]  
  
            if p.get("user_id") == get_cached_user_id():  
                delete_btn = ft.IconButton(  
                    icon=ft.Icons.DELETE_OUTLINE,  
                    icon_color="#64748b", icon_size=18,  
                    tooltip="Delete post",  
                    on_click=lambda e, post=p: handle_delete_post(post)  
                )  
                action_row_controls.append(delete_btn)  
            else:  
                report_btn = ft.IconButton(  
                    icon=ft.Icons.FLAG_OUTLINED,  
                    icon_color="#64748b", icon_size=18,  
                    tooltip="Report post",  
                    on_click=lambda e, pid=post_id: open_report_post_dialog(pid)  
                )  
                action_row_controls.append(report_btn)  
  
            post_body.append(ft.Row(action_row_controls, spacing=0))  
  
            public_feed_layout.controls.append(  
                ft.Container(  
                    content=ft.Column(post_body, spacing=6),  
                    padding=10, bgcolor="#1e293b", border_radius=8, width=340  
                )  
            )  
        page.update()  
  
    def render_friends_section(search_query=""):  
        friends_layout.controls.clear()  
        users = get_real_users(search_query)  
        if not users:  
            friends_layout.controls.append(  
                ft.Text("No students found. Try a different search!", color="#94a3b8", size=12)  
            )  
        for u in users:  
            uname = u.get("username", "Unknown")  
            detail_parts = [x for x in [u.get("department"), u.get("country")] if x]  
            detail_text = " · ".join(detail_parts) if detail_parts else "No details yet"  
  
            def view_this(e, name=uname):  
                load_other_profile(name)  
  
            def chat_this(e, name=uname):  
                conv_id, error = get_or_create_conversation(name)  
                if not error:  
                    set_panel_visibility(chats=True)  
                    open_thread(conv_id, name)  
  
            friends_layout.controls.append(  
                ft.Container(  
                    content=ft.Row([  
                        ft.Column([  
                            ft.Text(uname, color="white", weight="bold", size=13),  
                            ft.Text(detail_text, color="#94a3b8", size=11)  
                        ], spacing=2, expand=True),  
                        ft.Row([  
                            ft.IconButton(icon=ft.Icons.PERSON, icon_color="#6366f1",  
                                          tooltip="View profile", on_click=view_this),  
                            ft.IconButton(icon=ft.Icons.CHAT_BUBBLE_OUTLINE, icon_color="#10b981",  
                                          tooltip="Message", on_click=chat_this),  
                        ], spacing=0)  
                    ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),  
                    padding=8, bgcolor="#1e293b", border_radius=6, width=340  
                )  
            )  
        page.update()  
  
    def render_whisper_feed(reveal_names=False):  
        whisper_feed_layout.controls.clear()  
        blocked = get_blocked_ids()  
        posts = [w for w in get_whisper_posts() if w.get("user_id") not in blocked]  
        if not posts:  
            whisper_feed_layout.controls.append(  
                ft.Text("No secrets yet. Be the first to share one!", color="#94a3b8", size=12)  
            )  
        for w in posts:  
            real_name = w.get("username", "Unknown")  
            display_tag = f"Anonymous Ghost [Real: {real_name}]" if reveal_names else "Anonymous Ghost \U0001F47B"  
            header_color = "#eab308" if reveal_names else "#f43f5e"  
            whisper_feed_layout.controls.append(  
                ft.Container(  
                    content=ft.Column([  
                        ft.Row([ft.Icon(ft.Icons.SECURITY_OUTLINED, color=header_color), ft.Text(display_tag, weight=ft.FontWeight.BOLD, color=header_color)]),  
                        ft.Text(w.get("content", ""), color="#e2e8f0")  
                    ]), padding=12, bgcolor="#271c24", border_radius=10, width=340  
                )  
            )  
        page.update()  
  
    def handle_post_whisper(e):  
        content = (whisper_text_box.value or "").strip()  
        if not content:  
            whisper_status_text.value = "Write a secret first!"  
            whisper_status_text.color = "red"  
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
            whisper_status_text.color = "#10b981"  
            page.update()  
            render_whisper_feed(reveal_names=creator_admin_switch.value)  
        except Exception as ex:  
            whisper_status_text.value = f"Failed to post: {str(ex)}"  
            whisper_status_text.color = "red"  
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
                                    color="#94a3b8", size=13),  
                    padding=20, alignment=ft.Alignment.CENTER  
                )  
            )  
        for p in video_posts:  
            is_anon = p.get("is_anonymous", False)  
            display_name = "Anonymous Ghost \U0001F47B" if is_anon else p.get("username", "Unknown")  
            reels_layout.controls.append(  
                ft.Container(  
                    content=ft.Column([  
                        ft.Container(  
                            content=ft.Column([  
                                ft.Icon(ft.Icons.PLAY_CIRCLE_FILL, color="white", size=48),  
                                ft.Text("Tap to play", color="white", size=12)  
                            ], alignment=ft.MainAxisAlignment.CENTER,  
                               horizontal_alignment=ft.CrossAxisAlignment.CENTER),  
                            width=340, height=420, bgcolor="#1e293b", border_radius=12,  
                            alignment=ft.Alignment.CENTER,  
                            on_click=lambda e, url=p["media_url"]: page.launch_url(url)  
                        ),  
                        ft.Row([  
                            ft.Icon(ft.Icons.SECURITY_OUTLINED if is_anon else ft.Icons.ACCOUNT_CIRCLE,  
                                    color="#f43f5e" if is_anon else "#6366f1", size=16),  
                            ft.Text(display_name, weight=ft.FontWeight.BOLD,  
                                    color="#f43f5e" if is_anon else "#6366f1", size=13)  
                        ]),  
                        ft.Text(p.get("content") or "", color="#e2e8f0", size=12)  
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
        "like": (ft.Icons.FAVORITE, "#f43f5e"),  
        "comment": (ft.Icons.CHAT_BUBBLE, "#6366f1"),  
        "message": (ft.Icons.MAIL, "#10b981"),  
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
                ft.Text("No notifications yet.", color="#94a3b8", size=13)  
            )  
        for n in notifs:  
            icon, color = NOTIF_ICONS.get(n.get("type"), (ft.Icons.NOTIFICATIONS, "#94a3b8"))  
            is_unread = not n.get("is_read", True)  
            notifications_layout.controls.append(  
                ft.Container(  
                    content=ft.Row([  
                        ft.Icon(icon, color=color, size=20),  
                        ft.Text(n.get("message", ""), color="white" if is_unread else "#94a3b8", size=13, expand=True)  
                    ], spacing=10),  
                    padding=10,  
                    bgcolor="#27314a" if is_unread else "#1e293b",  
                    border_radius=8, width=340  
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
                nav_buttons["notifications"].icon = ft.Icons.NOTIFICATIONS_ACTIVE  
                nav_buttons["notifications"].icon_color = "#f43f5e"  
            else:  
                nav_buttons["notifications"].icon = ft.Icons.NOTIFICATIONS_NONE  
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
    NAV_ACTIVE = "#6366f1"  
    NAV_INACTIVE = "#94a3b8"  
    active_nav_key = {"value": "feed"}  
  
    def highlight_nav(active_key):  
        active_nav_key["value"] = active_key  
        for key, btn in nav_buttons.items():  
            if key == "notifications" and btn.icon == ft.Icons.NOTIFICATIONS_ACTIVE:  
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
        render_conversations_list()  
        highlight_nav("chats")  
  
    def nav_to_people(e):  
        set_panel_visibility(people=True)  
        render_friends_section()  
        highlight_nav("people")  
  
    def nav_to_reels(e):  
        set_panel_visibility(reels=True)  
        render_reels_feed()  
        highlight_nav("reels")  
  
    def nav_to_notifications(e):  
        set_panel_visibility(notifications=True)  
        render_notifications_panel()  
        highlight_nav("notifications")  
        nav_buttons["notifications"].icon = ft.Icons.NOTIFICATIONS_NONE  
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
  
    def handle_logout_from_menu(dlg):  
        close_menu_dialog(dlg)  
        page.run_task(handle_logout, None)  
  
    def open_blocked_users_dialog(menu_dlg=None):  
        if menu_dlg:  
            close_menu_dialog(menu_dlg)  
  
        blocked_list_col = ft.Column(spacing=8, scroll=ft.ScrollMode.AUTO, height=280)  
  
        def load_blocked_list():  
            blocked_list_col.controls.clear()  
            user_id = get_cached_user_id()  
            ids = list(get_blocked_ids(force_refresh=True))  
            if not ids:  
                blocked_list_col.controls.append(  
                    ft.Text("You haven't blocked anyone.", color="#94a3b8", size=12)  
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
            bgcolor="#1e293b",  
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
            bgcolor="#1e293b",  
            content=ft.Column([  
                ft.ListTile(  
                    leading=ft.Icon(ft.Icons.SETTINGS, color="#6366f1"),  
                    title=ft.Text("Settings", color="white"),  
                    subtitle=ft.Text("Change password, email & more", color="#94a3b8", size=11),  
                    on_click=lambda ev: open_settings_from_menu(dlg)  
                ),  
                ft.ListTile(  
                    leading=ft.Icon(ft.Icons.BLOCK, color="#f43f5e"),  
                    title=ft.Text("Blocked Users", color="white"),  
                    on_click=lambda ev: open_blocked_users_dialog(dlg)  
                ),  
                ft.ListTile(  
                    leading=ft.Icon(ft.Icons.DESCRIPTION_OUTLINED, color="#94a3b8"),  
                    title=ft.Text("Terms & Privacy Policy", color="white"),  
                    on_click=lambda ev: open_terms_dialog()  
                ),  
                ft.ListTile(  
                    leading=ft.Icon(ft.Icons.LOGOUT, color="#f43f5e"),  
                    title=ft.Text("Log Out", color="#f43f5e"),  
                    on_click=lambda ev: handle_logout_from_menu(dlg)  
                ),  
            ], tight=True),  
            actions=[ft.TextButton("Close", on_click=lambda ev: close_menu_dialog(dlg))]  
        )  
        page.overlay.append(dlg)  
        dlg.open = True  
        page.update()  
  
    def set_panel_visibility(feed=False, secrets=False, chats=False, people=False, reels=False, notifications=False, profile=False):  
        if not chats:  
            chat_state["polling_active"] = False  
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
        "feed":    ft.IconButton(icon=ft.Icons.HOME, icon_color=NAV_ACTIVE, tooltip="Feed", icon_size=20, style=NAV_BTN_STYLE),  
        "secrets": ft.IconButton(icon=ft.Icons.THEATER_COMEDY, icon_color=NAV_INACTIVE, tooltip="Secrets", icon_size=20, style=NAV_BTN_STYLE),  
        "people":  ft.IconButton(icon=ft.Icons.GROUPS, icon_color=NAV_INACTIVE, tooltip="Friends", icon_size=20, style=NAV_BTN_STYLE),  
        "chats":   ft.IconButton(icon=ft.Icons.CHAT_BUBBLE, icon_color=NAV_INACTIVE, tooltip="Chats", icon_size=20, style=NAV_BTN_STYLE),  
        "reels":   ft.IconButton(icon=ft.Icons.VIDEO_LIBRARY, icon_color=NAV_INACTIVE, tooltip="Reels", icon_size=20, style=NAV_BTN_STYLE),  
        "notifications": ft.IconButton(icon=ft.Icons.NOTIFICATIONS_NONE, icon_color=NAV_INACTIVE, tooltip="Notifications", icon_size=20, style=NAV_BTN_STYLE),  
        "profile": ft.IconButton(icon=ft.Icons.PERSON, icon_color=NAV_INACTIVE, tooltip="Profile", icon_size=20, style=NAV_BTN_STYLE),  
    }  
    nav_buttons["feed"].on_click = nav_to_feed  
    nav_buttons["secrets"].on_click = nav_to_secrets  
    nav_buttons["people"].on_click = nav_to_people  
    nav_buttons["chats"].on_click = nav_to_chats  
    nav_buttons["reels"].on_click = nav_to_reels  
    nav_buttons["notifications"].on_click = nav_to_notifications  
    nav_buttons["profile"].on_click = nav_to_profile  
  
    menu_button = ft.IconButton(icon=ft.Icons.MENU, icon_color=NAV_INACTIVE, tooltip="Menu",  
                                icon_size=20, style=NAV_BTN_STYLE, on_click=open_main_menu)  
  
    # scroll=AUTO is a safety net — even on very narrow phones where icons  
    # still don't all fit, every icon stays reachable by swiping sideways  
    # instead of being invisibly pushed off-screen like before.  
    custom_nav_bar = ft.Container(  
        content=ft.Row([  
            nav_buttons["feed"], nav_buttons["secrets"], nav_buttons["people"],  
            nav_buttons["chats"], nav_buttons["reels"], nav_buttons["notifications"],  
            nav_buttons["profile"], menu_button  
        ], alignment=ft.MainAxisAlignment.START, spacing=2, scroll=ft.ScrollMode.AUTO),  
        padding=ft.Padding.symmetric(vertical=6),  
        bgcolor="#1e293b"  
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
                                           fit=ft.BoxFit.COVER, border_radius=10)  
            except Exception as ex:  
                print(f"Preview render failed: {ex}")  
                preview_content = ft.Icon(ft.Icons.IMAGE, size=60, color="#6366f1")  
        else:  
            preview_content = ft.Column([  
                ft.Icon(ft.Icons.PLAY_CIRCLE_FILL, size=48, color="white"),  
                ft.Text(selected_media["name"] or "video", color="white", size=11)  
            ], alignment=ft.MainAxisAlignment.CENTER, horizontal_alignment=ft.CrossAxisAlignment.CENTER)  
  
        media_preview_container.content = ft.Stack([  
            ft.Container(content=preview_content, width=160, height=160,  
                        bgcolor="#1e293b", border_radius=10, alignment=ft.Alignment.CENTER),  
            ft.Container(  
                content=ft.IconButton(icon=ft.Icons.CANCEL, icon_color="#f43f5e",  
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
            media_status_text.color = "red"  
            page.update()  
            return  
  
        if not f.bytes:  
            media_status_text.value = "Couldn't read that file — try again."  
            media_status_text.color = "red"  
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
            media_status_text.color = "red"  
            page.update()  
            return  
  
        set_composer_busy(True)  
        media_status_text.value = "Posting..."  
        media_status_text.color = "#94a3b8"  
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
            media_status_text.color = "red"  
            page.update()  
  
    send_button = ft.IconButton(icon=ft.Icons.SEND, icon_color="#6366f1", on_click=handle_create_post)  
    photo_button = ft.IconButton(icon=ft.Icons.PHOTO_LIBRARY_OUTLINED, icon_color="#6366f1", tooltip="Add photo or video", on_click=open_media_picker)  
  
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
  
    panel_people = ft.Column([  
        ft.Text("Find Friends", size=18, weight=ft.FontWeight.BOLD, color="white"),  
        ft.Row([search_input, ft.Icon(ft.Icons.SEARCH, color="#94a3b8")], alignment=ft.MainAxisAlignment.CENTER),  
        friends_layout  
    ], visible=False, horizontal_alignment=ft.CrossAxisAlignment.CENTER)  
  
    # --- TAB 2: SECRETS ---  
    whisper_text_box = ft.TextField(hint_text="Share a school secret anonymously...", width=260, dense=True, color="white")  
    whisper_status_text = ft.Text("", size=11)  
    creator_admin_switch = ft.Switch(value=False, on_change=lambda e: render_whisper_feed(reveal_names=creator_admin_switch.value))  
  
    panel_whisper_wall = ft.Column([  
        ft.Text("The Whisper Wall \U0001F92B", size=18, weight=ft.FontWeight.BOLD, color="#f43f5e"),  
        ft.Row([ft.Text("Creator Key (Reveal Identity)", color="white"), creator_admin_switch], alignment=ft.MainAxisAlignment.CENTER),  
        ft.Row([whisper_text_box, ft.IconButton(icon=ft.Icons.SEND, icon_color="#f43f5e", on_click=handle_post_whisper)], alignment=ft.MainAxisAlignment.CENTER),  
        whisper_status_text,  
        ft.Divider(height=10, color="#CBD3DD"),  
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
            # Look up the target user's profile  
            profile_resp = supabase.table("profiles").select("user_id, username").eq("username", target_username).execute()  
            if not profile_resp.data:  
                return None, f"No user found with username '{target_username}'."  
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
            return False  
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
            return True  
        except Exception as e:  
            print(f"Error sending message: {e}")  
            return False  
  
    chat_state = {"conversation_id": None, "other_username": None, "polling_active": False, "last_rendered_count": -1}  
  
    conversations_layout = ft.Column(spacing=8, scroll=ft.ScrollMode.ALWAYS, height=260)  
    new_chat_input = ft.TextField(hint_text="Start a chat (enter username)", width=220, dense=True, color="white")  
    chat_inbox_status = ft.Text("", size=12)  
  
    thread_messages_layout = ft.Column(spacing=8, scroll=ft.ScrollMode.ALWAYS, height=260, auto_scroll=True)  
    thread_input_box = ft.TextField(hint_text="Type a message...", width=220, dense=True, color="white")  
    thread_header_text = ft.Text("", size=16, weight=ft.FontWeight.BOLD, color="white")  
    thread_status = ft.Text("", size=11)  
  
    def render_conversations_list():  
        conversations_layout.controls.clear()  
        convs = get_conversations()  
        if not convs:  
            conversations_layout.controls.append(ft.Text("No chats yet. Start one below!", color="#94a3b8", size=12))  
        for c in convs:  
            def open_this(e, cid=c["conversation_id"], uname=c["other_username"]):  
                open_thread(cid, uname)  
  
            conversations_layout.controls.append(  
                ft.Container(  
                    content=ft.Column([  
                        ft.Text(c["other_username"], weight=ft.FontWeight.BOLD, color="#10b981", size=14),  
                        ft.Text(c["last_message"], color="#e2e8f0", size=12, max_lines=1)  
                    ]),  
                    padding=10, bgcolor="#1e293b", border_radius=8, width=320,  
                    on_click=open_this  
                )  
            )  
        page.update()  
  
    def handle_start_new_chat(e):  
        target = (new_chat_input.value or "").strip()  
        if not target:  
            chat_inbox_status.value = "Enter a username first."  
            chat_inbox_status.color = "red"  
            page.update()  
            return  
        conv_id, error = get_or_create_conversation(target)  
        if error:  
            chat_inbox_status.value = error  
            chat_inbox_status.color = "red"  
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
            bubble_color = "#6366f1" if is_mine else "#1e293b"  
            align = ft.MainAxisAlignment.END if is_mine else ft.MainAxisAlignment.START  
            thread_messages_layout.controls.append(  
                ft.Row([  
                    ft.Container(  
                        content=ft.Text(m.get("content", ""), color="white", size=13),  
                        padding=10, bgcolor=bubble_color, border_radius=10, width=220  
                    )  
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
        render_conversations_list()  
        page.update()  
  
    def handle_send_thread_message(e):  
        content = thread_input_box.value or ""  
        if not content.strip():  
            return  
        if send_message(chat_state["conversation_id"], content):  
            thread_input_box.value = ""  
            page.update()  
            render_thread_messages()  
        else:  
            thread_status.value = "Message failed to send."  
            thread_status.color = "red"  
            page.update()  
  
    panel_chats_inbox = ft.Column([  
        ft.Text("Direct Messages \U0001F4AC", size=18, weight=ft.FontWeight.BOLD, color="#10b981"),  
        ft.Row([new_chat_input, ft.IconButton(icon=ft.Icons.SEND, icon_color="#10b981", on_click=handle_start_new_chat)], alignment=ft.MainAxisAlignment.CENTER),  
        chat_inbox_status,  
        ft.Divider(height=10, color="#E6F0FF"),  
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
            spacing=4, run_spacing=4, height=220, width=320  
        )  
        for em in QUICK_EMOJIS:  
            grid.controls.append(  
                ft.TextButton(content=ft.Text(em, size=20), on_click=insert_emoji(em))  
            )  
  
        dlg = ft.AlertDialog(  
            title=ft.Text("Emoji", color="white", size=14),  
            bgcolor="#1e293b",  
            content=grid,  
            actions=[ft.TextButton("Close", on_click=lambda e: close_dlg(dlg))]  
        )  
        page.overlay.append(dlg)  
        dlg.open = True  
        page.update()  
  
    panel_chats_thread = ft.Column([  
        ft.Row([  
            ft.IconButton(icon=ft.Icons.ARROW_BACK, icon_color="#10b981", on_click=close_thread),  
            thread_header_text  
        ], alignment=ft.MainAxisAlignment.START),  
        thread_messages_layout,  
        thread_status,  
        ft.Row([  
            thread_input_box,  
            ft.IconButton(icon=ft.Icons.EMOJI_EMOTIONS_OUTLINED, icon_color="#94a3b8",  
                          tooltip="Emoji", on_click=lambda e: open_emoji_picker(thread_input_box)),  
            ft.IconButton(icon=ft.Icons.SEND, icon_color="#10b981", on_click=handle_send_thread_message)  
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
    profile_username_label = ft.Text("", size=15, weight=ft.FontWeight.BOLD, color="#6366f1")  
    profile_bio = ft.TextField(label="Bio (optional)", width=300, color="white",  
                               multiline=True, max_lines=3, border_color="#6366f1")  
    profile_school = ft.TextField(label="School / University", width=300,  
                                  color="white", border_color="#6366f1")  
    profile_password = ft.TextField(label="New Password (leave blank to keep)", password=True,  
                                    width=300, color="white", border_color="#6366f1")  
  
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
                                    width=280, color="white", border_color="#6366f1")  
    settings_email = ft.TextField(label="Change Email", width=280,  
                                  color="white", border_color="#6366f1")  
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
                settings_status.color = "#10b981"  
            else:  
                settings_status.value = "Nothing to update."  
                settings_status.color = "#94a3b8"  
            page.update()  
        except Exception as ex:  
            settings_status.value = f"Update failed: {str(ex)}"  
            settings_status.color = "red"  
            page.update()  
  
    def close_settings_dialog(d):  
        d.open = False  
        page.update()  
  
    def open_account_settings(e):  
        settings_email.value = user_cache.get("email", "")  
        settings_status.value = ""  
        dlg = ft.AlertDialog(  
            title=ft.Text("Account Settings", color="white", size=16),  
            bgcolor="#1e293b",  
            content=ft.Column([  
                settings_email,  
                profile_password,  
                settings_status  
            ], tight=True, spacing=12),  
            actions=[  
                ft.TextButton("Save", on_click=handle_save_account_settings),  
                ft.TextButton("Close", on_click=lambda ev: close_settings_dialog(dlg))  
            ]  
        )  
        page.overlay.append(dlg)  
        dlg.open = True  
        page.update()  
  
  
    def load_own_profile():  
        user_id = get_cached_user_id()  
        if not user_id:  
            return  
        try:  
            resp = supabase.table("profiles").select("*").eq("user_id", user_id).execute()  
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
            profile_status_text.color = "red"  
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
            profile_status_text.color = "#10b981"  
            page.update()  
        except Exception as ex:  
            profile_status_text.value = f"Avatar upload failed: {str(ex)}"  
            profile_status_text.color = "red"  
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
            profile_status_text.color = "#10b981"  
            page.update()  
        except Exception as ex:  
            profile_status_text.value = f"Save failed: {str(ex)}"  
            profile_status_text.color = "red"  
            page.update()  
  
    profile_edit_content = ft.Column([  
        ft.Row([  
            profile_avatar_img,  
            ft.Column([  
                profile_username_label,  
                ft.ElevatedButton(  
                    content=ft.Text("Change Photo", size=11, color="white"),  
                    bgcolor="#6366f1", on_click=handle_upload_avatar, height=32  
                )  
            ], spacing=6)  
        ], alignment=ft.MainAxisAlignment.CENTER, spacing=16),  
        profile_bio,  
        profile_school,  
        dept_dd,  
        country_dd,  
        state_dd,  
        lga_dd,  
        ft.ElevatedButton(  
            content=ft.Text("Save Profile", color="white"),  
            bgcolor="#6366f1", width=300, on_click=handle_save_profile  
        ),  
        profile_status_text  
    ], spacing=12, horizontal_alignment=ft.CrossAxisAlignment.CENTER)  
  
    # --- VIEW OTHER USER'S PROFILE ---  
    view_profile_avatar = ft.Image(  
        src="https://ui-avatars.com/api/?background=6366f1&color=fff&size=80&name=U",  
        width=80, height=80, fit=ft.BoxFit.COVER, border_radius=40  
    )  
    view_profile_username = ft.Text("", size=18, weight=ft.FontWeight.BOLD, color="#6366f1")  
    view_profile_bio      = ft.Text("", color="#e2e8f0", size=13, italic=True)  
    view_profile_school   = ft.Text("", color="#e2e8f0", size=13)  
    view_profile_dept     = ft.Text("", color="#e2e8f0", size=13)  
    view_profile_country  = ft.Text("", color="#e2e8f0", size=13)  
    view_profile_state    = ft.Text("", color="#e2e8f0", size=13)  
    view_profile_lga      = ft.Text("", color="#e2e8f0", size=13)  
  
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
            view_profile_avatar.src = avatar if avatar else (
                f"https://ui-avatars.com/api/?background=6366f1&color=fff&size=80&name={uname}"
            )
            view_profile_bio.value     = p.get("bio") or ""
            view_profile_school.value  = f"\U0001F3EB  {p['school']}"  if p.get("school")           else ""  
            view_profile_dept.value    = f"\U0001F4DA  {p['department']}" if p.get("department")     else ""  
            view_profile_country.value = f"\U0001F30D  {p['country']}"  if p.get("country")          else ""  
            view_profile_state.value   = f"\U0001F4CD  {p['state']}"    if p.get("state")            else ""  
            view_profile_lga.value     = f"\U0001F3D8  {p['local_government']}" if p.get("local_government") else ""  
            panel_view_profile.visible = True  
            panel_settings.visible     = False  
            panel_home_feed.visible    = False  
            panel_whisper_wall.visible = False  
            panel_messages.visible     = False  
            panel_people.visible       = False  
            panel_reels.visible        = False  
            panel_notifications.visible = False  
            page.update()  
        except Exception as ex:  
            print(f"Error loading other profile: {ex}")  
  
    def close_profile_view(e):  
        panel_view_profile.visible = False  
        set_panel_visibility(feed=True)  
        render_public_feed()  
  
    def handle_block_from_profile(e):  
        target_id = viewed_profile_state["user_id"]  
        target_name = viewed_profile_state["username"]  
        if not target_id:  
            return  
        if block_user_action(target_id):  
            profile_view_status.value = f"@{target_name} has been blocked."  
            profile_view_status.color = "#10b981"  
        else:  
            profile_view_status.value = "Couldn't block — try again."  
            profile_view_status.color = "red"  
        page.update()  
  
    def open_report_user_dialog(e):  
        reason_dd = ft.Dropdown(  
            label="Reason", width=260, color="white",  
            options=[ft.dropdown.Option(r) for r in REPORT_REASONS]  
        )  
        status = ft.Text("", size=11)  
  
        def close_dlg(d):  
            d.open = False  
            page.update()  
  
        def submit_report(ev):  
            if not reason_dd.value:  
                status.value = "Please choose a reason."  
                status.color = "red"  
                page.update()  
                return  
            if report_user_action(viewed_profile_state["user_id"], reason_dd.value):  
                status.value = "Reported. Our team will review it."  
                status.color = "#10b981"  
                page.update()  
            else:  
                status.value = "Couldn't submit report — try again."  
                status.color = "red"  
                page.update()  
  
        dlg = ft.AlertDialog(  
            title=ft.Text(f"Report @{viewed_profile_state['username']}", color="white", size=15),  
            bgcolor="#1e293b",  
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
            ft.IconButton(icon=ft.Icons.ARROW_BACK, icon_color="#6366f1", on_click=close_profile_view),  
            ft.Text("Profile", size=16, weight=ft.FontWeight.BOLD, color="white")  
        ]),  
        view_profile_avatar,  
        view_profile_username,  
        view_profile_bio,  
        ft.Divider(color="#334155"),  
        view_profile_school,  
        view_profile_dept,  
        view_profile_country,  
        view_profile_state,  
        view_profile_lga,  
        ft.ElevatedButton(  
            content=ft.Text("Send Message", color="white"),  
            bgcolor="#10b981", width=280,  
            on_click=lambda e: handle_start_chat_from_profile()  
        ),  
        ft.Row([  
            ft.TextButton(  
                content=ft.Row([ft.Icon(ft.Icons.BLOCK, color="#f43f5e", size=16),  
                                ft.Text("Block", color="#f43f5e", size=12)], spacing=4),  
                on_click=handle_block_from_profile  
            ),  
            ft.TextButton(  
                content=ft.Row([ft.Icon(ft.Icons.FLAG_OUTLINED, color="#94a3b8", size=16),  
                                ft.Text("Report", color="#94a3b8", size=12)], spacing=4),  
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
            ui_message.color = "red"  
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
                    ui_message.color = "red"  
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
            ui_message.color = "red"  
            page.update()  
  
    def handle_resend_confirmation(e):  
        if not input_login_email.value or "@" not in input_login_email.value:  
            ui_message.value = "Enter your email address above first, then tap Resend."  
            ui_message.color = "red"  
            page.update()  
            return  
        try:  
            supabase.auth.resend({"type": "signup", "email": input_login_email.value})  
            ui_message.value = "Confirmation email resent — check your inbox."  
            ui_message.color = "green"  
            page.update()  
        except Exception as ex:  
            ui_message.value = f"Couldn't resend: {str(ex)}"  
            ui_message.color = "red"  
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
            bgcolor="#1e293b",  
            content=ft.Column(  
                [ft.Text(TERMS_TEXT, color="#e2e8f0", size=12)],  
                scroll=ft.ScrollMode.AUTO, height=400, width=320  
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
            reg_step1_status.color = "red"  
            page.update()  
            return  
        if not agree_terms_checkbox.value:  
            reg_step1_status.value = "You must agree to the Terms of Service & Privacy Policy to continue."  
            reg_step1_status.color = "red"  
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
            reg_step2_status.color = "#94a3b8"  
            page.update()  
        except Exception as ex:  
            reg_step1_status.value = f"Couldn't send code: {str(ex)}"  
            reg_step1_status.color = "red"  
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
            reg_step2_status.color = "#10b981"  
            page.update()  
        except Exception as ex:  
            reg_step2_status.value = f"Couldn't resend: {str(ex)}"  
            reg_step2_status.color = "red"  
            page.update()  
  
    def handle_verify_reg_otp(e):  
        code = (input_reg_otp.value or "").strip()  
        if not code:  
            reg_step2_status.value = "Enter the 6-digit code."  
            reg_step2_status.color = "red"  
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
                reg_step2_status.color = "red"  
                page.update()  
                return  
  
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
            reg_step2_status.color = "red"  
            page.update()  
  
    async def handle_finalize_registration(e):  
        if not input_reg_password.value or not input_reg_confirm.value:  
            reg_step3_status.value = "Please fill in both password fields."  
            reg_step3_status.color = "red"  
            page.update()  
            return  
        if input_reg_password.value != input_reg_confirm.value:  
            reg_step3_status.value = "Passwords do not match."  
            reg_step3_status.color = "red"  
            page.update()  
            return  
        try:  
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
            reg_step3_status.color = "red"  
            page.update()  
  
    reg_step1 = ft.Column([  
        ft.Text("Create Account", size=18, weight=ft.FontWeight.BOLD, color="white"),  
        input_reg_username,  
        input_reg_email,  
        ft.Row([  
            agree_terms_checkbox,  
            ft.Text("I agree to the", color="#94a3b8", size=12),  
            ft.TextButton(content=ft.Text("Terms & Privacy Policy", color="#6366f1", size=12), on_click=open_terms_dialog)  
        ], spacing=0),  
        ft.ElevatedButton(content=ft.Text("Next", color="white"), on_click=handle_reg_step1_next, width=300, bgcolor="#10b981"),  
        reg_step1_status,  
        ft.TextButton(content=ft.Text("Already have an account? Log in", color="#94a3b8"), on_click=switch_to_login)  
    ], visible=False, horizontal_alignment=ft.CrossAxisAlignment.CENTER)  
  
    reg_step2 = ft.Column([  
        ft.Text("Verify Your Email", size=18, weight=ft.FontWeight.BOLD, color="white"),  
        input_reg_otp,  
        ft.ElevatedButton(content=ft.Text("Next", color="white"), on_click=handle_verify_reg_otp, width=300, bgcolor="#10b981"),  
        reg_step2_status,  
        ft.TextButton(content=ft.Text("Resend code", color="#94a3b8", size=12), on_click=handle_resend_reg_otp)  
    ], visible=False, horizontal_alignment=ft.CrossAxisAlignment.CENTER)  
  
    reg_step3 = ft.Column([  
        ft.Text("Set Your Password", size=18, weight=ft.FontWeight.BOLD, color="white"),  
        input_reg_password,  
        input_reg_confirm,  
        ft.ElevatedButton(content=ft.Text("Create Account", color="white"), on_click=handle_finalize_registration, width=300, bgcolor="#10b981"),  
        reg_step3_status  
    ], visible=False, horizontal_alignment=ft.CrossAxisAlignment.CENTER)  
  
    layout_login_form = ft.Column([  
        input_login_email,  
        input_login_password,  
        ft.ElevatedButton(content=ft.Text("Log In", color="white"), on_click=handle_login, width=300, bgcolor="#6366f1"),  
        ft.TextButton(content=ft.Text("New here? Create an account", color="#94a3b8"), on_click=switch_to_register),  
        ft.TextButton(content=ft.Text("Resend confirmation email", color="#94a3b8", size=12), on_click=handle_resend_confirmation)  
    ], horizontal_alignment=ft.CrossAxisAlignment.CENTER)  
  
    layout_auth_master = ft.Column([  
        ft.Text("UniVibe", size=36, weight=ft.FontWeight.BOLD, color="#6366f1"),  
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
                # Restore the Supabase auth session  
                try:  
                    supabase.auth.set_session(access_token, refresh_token)  
                    supabase.postgrest.auth(access_token)  
                except Exception as ex:  
                    print(f"set_session warning: {ex}")  
  
                # Rebuild the user cache directly from stored values —  
                # never call get_user() here, it fails on the sync client  
                user_cache["id"]           = user_id  
                user_cache["email"]        = user_email  
                user_cache["access_token"] = access_token  
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
