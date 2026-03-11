import json, os

DATA_DIR = os.path.dirname(os.path.abspath(__file__))

# ═══════════════════════════════════════════════════════════════════════
# COMPREHENSIVE MILITARY BASES DATABASE — 600+ ENTRIES
# Sources: Wikipedia, GlobalSecurity, IISS Military Balance, OpenStreetMap,
#          Jane's Defence Weekly (public data), community OSINT, DoD BSIR
# All coordinates approximate — educational/OSINT purposes only
# ═══════════════════════════════════════════════════════════════════════

bases = [
  # ─── INDIA — AIR FORCE (62 stations) ────────────────────────────────
  {"id":"in_af_agra","name":"Agra Air Force Station","lat":27.158,"lon":77.961,"country":"India","cc":"IN","type":"air_base","arm":"IAF","status":"active","desc":"Transport hub, C-17 Globemaster III, C-130J","details":{"role":"Strategic airlift","aircraft":["C-17","C-130J","An-32"],"established":"1947","runways":"1 × 2,900m"}},
  {"id":"in_af_ambala","name":"Ambala Air Force Station","lat":30.380,"lon":76.822,"country":"India","cc":"IN","type":"air_base","arm":"IAF","status":"active","desc":"No.17 Golden Arrows Sqn, Rafale fighters","details":{"role":"Strike","aircraft":["Rafale","Jaguar"],"established":"1948","runways":"1 × 2,800m","notable":"First Rafale base in India"}},
  {"id":"in_af_awantipur","name":"Awantipur Air Force Station","lat":33.775,"lon":75.020,"country":"India","cc":"IN","type":"air_base","arm":"IAF","status":"active","desc":"Kashmir Valley forward base","details":{"role":"Air defense, CAS","aircraft":["MiG-21","Mi-17"],"runways":"1 × 2,700m"}},
  {"id":"in_af_bagdogra","name":"Bagdogra Air Force Station","lat":26.681,"lon":88.323,"country":"India","cc":"IN","type":"air_base","arm":"IAF","status":"active","desc":"Siliguri Corridor, northeast gateway","details":{"role":"Air defense","aircraft":["Su-30MKI"],"runways":"1 × 2,700m","notable":"Guards Chicken's Neck corridor"}},
  {"id":"in_af_bareilly","name":"Bareilly Air Force Station","lat":28.422,"lon":79.451,"country":"India","cc":"IN","type":"air_base","arm":"IAF","status":"active","desc":"Jaguar maritime strike","details":{"role":"Maritime strike","aircraft":["Jaguar IM"],"runways":"1 × 2,700m"}},
  {"id":"in_af_bhuj","name":"Bhuj Air Force Station","lat":23.288,"lon":69.670,"country":"India","cc":"IN","type":"air_base","arm":"IAF","status":"active","desc":"Gujarat, Pakistan border air defense","details":{"role":"Forward air defense","runways":"1 × 2,500m","notable":"Key role in 1971 war"}},
  {"id":"in_af_bidar","name":"Bidar Air Force Station","lat":17.908,"lon":77.488,"country":"India","cc":"IN","type":"air_base","arm":"IAF","status":"active","desc":"Training base, Karnataka","details":{"role":"Operational Training Unit","aircraft":["Kiran","Hawk"],"runways":"1 × 2,400m"}},
  {"id":"in_af_nal","name":"NAL Air Force Station (Bikaner)","lat":28.071,"lon":73.208,"country":"India","cc":"IN","type":"air_base","arm":"IAF","status":"active","desc":"Rajasthan desert forward base","details":{"role":"Forward strike","runways":"1 × 2,500m"}},
  {"id":"in_af_carnicobar","name":"INS Baaz / Car Nicobar AFS","lat":9.153,"lon":92.822,"country":"India","cc":"IN","type":"air_base","arm":"IAF/Navy","status":"active","desc":"Andaman & Nicobar, Malacca Strait watch","details":{"role":"Maritime patrol, forward air","runways":"1 × 3,000m","notable":"Southernmost IAF base"}},
  {"id":"in_af_chabua","name":"Chabua Air Force Station","lat":27.478,"lon":95.113,"country":"India","cc":"IN","type":"air_base","arm":"IAF","status":"active","desc":"Assam, northeast operations","details":{"role":"Transport, helicopter ops","aircraft":["Mi-17","Dhruv"],"runways":"1 × 2,500m"}},
  {"id":"in_af_chandigarh","name":"Chandigarh Air Force Station","lat":30.674,"lon":76.789,"country":"India","cc":"IN","type":"air_base","arm":"IAF","status":"active","desc":"Western Air Command base","details":{"role":"Fighter ops","aircraft":["MiG-21"],"runways":"1 × 2,700m"}},
  {"id":"in_af_coimbatore","name":"Sulur Air Force Station","lat":11.030,"lon":77.043,"country":"India","cc":"IN","type":"air_base","arm":"IAF","status":"active","desc":"Tamil Nadu, Su-30MKI","details":{"role":"Air superiority","aircraft":["Su-30MKI","LCA Tejas"],"runways":"1 × 2,700m","notable":"First LCA Tejas operational base"}},
  {"id":"in_af_dbo","name":"Daulat Beg Oldie ALG","lat":35.376,"lon":77.686,"country":"India","cc":"IN","type":"air_base","arm":"IAF","status":"active","desc":"World's highest airstrip at 5,065m","details":{"role":"Forward logistics, LAC patrol","runways":"1 × short","notable":"World's highest landing strip"}},
  {"id":"in_af_dundigal","name":"Air Force Academy Dundigal","lat":17.612,"lon":78.102,"country":"India","cc":"IN","type":"training","arm":"IAF","status":"active","desc":"IAF officer training academy","details":{"role":"Training","aircraft":["PC-7 Mk II","Pilatus","Hawk"],"runways":"2 × 2,400m"}},
  {"id":"in_af_gorakhpur","name":"Gorakhpur Air Force Station","lat":26.741,"lon":83.449,"country":"India","cc":"IN","type":"air_base","arm":"IAF","status":"active","desc":"UP, eastern operations","details":{"role":"Fighter ops","aircraft":["Su-30MKI"],"runways":"1 × 2,700m"}},
  {"id":"in_af_gwalior","name":"Gwalior Air Force Station","lat":26.292,"lon":78.227,"country":"India","cc":"IN","type":"air_base","arm":"IAF","status":"active","desc":"Mirage 2000, nuclear-capable","details":{"role":"Nuclear strike","aircraft":["Mirage 2000H","MiG-21"],"runways":"1 × 2,800m","notable":"Nuclear delivery capable"}},
  {"id":"in_af_halwara","name":"Halwara Air Force Station","lat":30.732,"lon":75.639,"country":"India","cc":"IN","type":"air_base","arm":"IAF","status":"active","desc":"Punjab, Rafale forward base","details":{"role":"Strike","aircraft":["Rafale","MiG-29"],"runways":"1 × 2,700m"}},
  {"id":"in_af_hashimara","name":"Hashimara Air Force Station","lat":26.715,"lon":89.378,"country":"India","cc":"IN","type":"air_base","arm":"IAF","status":"active","desc":"West Bengal, Bhutan/China border","details":{"role":"Air defense","aircraft":["Su-30MKI"],"runways":"1 × 2,500m"}},
  {"id":"in_af_hindon","name":"Hindon Air Force Station","lat":28.709,"lon":77.430,"country":"India","cc":"IN","type":"air_base","arm":"IAF","status":"active","desc":"NCR region, transport hub","details":{"role":"Strategic transport","aircraft":["C-17","C-130J","Il-76","An-32"],"runways":"1 × 2,800m","notable":"Largest IAF base by aircraft"}},
  {"id":"in_af_jaisalmer","name":"Jaisalmer Air Force Station","lat":26.909,"lon":70.865,"country":"India","cc":"IN","type":"air_base","arm":"IAF","status":"active","desc":"Rajasthan desert, Pakistan border","details":{"role":"Forward fighter ops","runways":"1 × 2,500m","notable":"Near Pokhran test range"}},
  {"id":"in_af_jamnagar","name":"Jamnagar Air Force Station","lat":22.461,"lon":70.012,"country":"India","cc":"IN","type":"air_base","arm":"IAF","status":"active","desc":"Gujarat coast","details":{"role":"Maritime patrol","runways":"1 × 2,500m"}},
  {"id":"in_af_jodhpur","name":"Jodhpur Air Force Station","lat":26.251,"lon":72.949,"country":"India","cc":"IN","type":"air_base","arm":"IAF","status":"active","desc":"Rajasthan, Pakistan border ops","details":{"role":"Air defense","aircraft":["Su-30MKI","MiG-21"],"runways":"1 × 2,800m"}},
  {"id":"in_af_jorhat","name":"Jorhat Air Force Station","lat":26.732,"lon":94.176,"country":"India","cc":"IN","type":"air_base","arm":"IAF","status":"active","desc":"Assam, northeast India","details":{"role":"Transport, helicopter","aircraft":["Mi-17","Dhruv","Chinook"],"runways":"1 × 2,500m"}},
  {"id":"in_af_kalaikunda","name":"Kalaikunda Air Force Station","lat":22.326,"lon":87.203,"country":"India","cc":"IN","type":"air_base","arm":"IAF","status":"active","desc":"West Bengal, maritime ops","details":{"role":"Maritime strike","aircraft":["Jaguar"],"runways":"1 × 2,700m"}},
  {"id":"in_af_leh","name":"Leh Kushok Bakula Air Base","lat":34.136,"lon":77.547,"country":"India","cc":"IN","type":"air_base","arm":"IAF","status":"active","desc":"Ladakh, world's highest air base at 3,256m","details":{"role":"Forward air defense, China LAC","aircraft":["C-130J","An-32","MiG-29"],"runways":"1 × 2,700m","notable":"Highest operational air base"}},
  {"id":"in_af_naliya","name":"Naliya Air Force Station","lat":23.220,"lon":68.832,"country":"India","cc":"IN","type":"air_base","arm":"IAF","status":"active","desc":"Gujarat, Kutch border region","details":{"role":"Air defense","aircraft":["Su-30MKI"],"runways":"1 × 2,500m"}},
  {"id":"in_af_pathankot","name":"Pathankot Air Force Station","lat":32.234,"lon":75.635,"country":"India","cc":"IN","type":"air_base","arm":"IAF","status":"active","desc":"Punjab, frontline base","details":{"role":"Strike","aircraft":["MiG-21","Jaguar"],"runways":"1 × 2,700m","notable":"Terror attack Jan 2016"}},
  {"id":"in_af_pune","name":"Lohegaon Air Force Station (Pune)","lat":18.582,"lon":73.920,"country":"India","cc":"IN","type":"air_base","arm":"IAF","status":"active","desc":"Maharashtra, MiG-29 fighters","details":{"role":"Air defense","aircraft":["MiG-29"],"runways":"1 × 2,700m"}},
  {"id":"in_af_srinagar","name":"Srinagar Air Force Station","lat":34.005,"lon":74.774,"country":"India","cc":"IN","type":"air_base","arm":"IAF","status":"active","desc":"J&K, forward operations","details":{"role":"CAS, air defense","aircraft":["MiG-21","Mi-17"],"runways":"1 × 2,700m"}},
  {"id":"in_af_tezpur","name":"Tezpur Air Force Station","lat":26.709,"lon":92.784,"country":"India","cc":"IN","type":"air_base","arm":"IAF","status":"active","desc":"Assam, near China border","details":{"role":"Air superiority","aircraft":["Su-30MKI"],"runways":"1 × 2,700m","notable":"Key China border defense"}},
  {"id":"in_af_thanjavur","name":"Thanjavur Air Force Station","lat":10.722,"lon":79.101,"country":"India","cc":"IN","type":"air_base","arm":"IAF","status":"active","desc":"Tamil Nadu, Su-30MKI maritime","details":{"role":"Maritime strike","aircraft":["Su-30MKI (BrahMos)"],"runways":"1 × 2,700m","notable":"BrahMos equipped Su-30s"}},
  {"id":"in_af_uttarlai","name":"Uttarlai Air Force Station","lat":25.690,"lon":71.790,"country":"India","cc":"IN","type":"air_base","arm":"IAF","status":"active","desc":"Rajasthan, Pakistan border","details":{"role":"Forward ops","runways":"1 × 2,500m"}},
  {"id":"in_af_yelahanka","name":"Yelahanka Air Force Station","lat":13.135,"lon":77.600,"country":"India","cc":"IN","type":"air_base","arm":"IAF","status":"active","desc":"Bengaluru, Aero India venue","details":{"role":"Training, airshow","runways":"1 × 2,500m","notable":"Aero India biennial airshow"}},
  {"id":"in_af_tambaram","name":"Tambaram Air Force Station","lat":12.920,"lon":80.110,"country":"India","cc":"IN","type":"air_base","arm":"IAF","status":"active","desc":"Chennai suburb, helicopter ops","details":{"role":"Helicopter training","aircraft":["Mi-8","Dhruv"],"runways":"1 × 2,400m"}},
  {"id":"in_af_begumpet","name":"Begumpet Air Force Station","lat":17.450,"lon":78.470,"country":"India","cc":"IN","type":"air_base","arm":"IAF","status":"active","desc":"Hyderabad, communication hub","details":{"role":"Signals, communication","runways":"1 × 2,400m"}},
  {"id":"in_af_suratgarh","name":"Suratgarh Air Force Station","lat":29.330,"lon":73.850,"country":"India","cc":"IN","type":"air_base","arm":"IAF","status":"active","desc":"Rajasthan, Pakistan border","details":{"role":"Fighter ops","aircraft":["Su-30MKI"],"runways":"1 × 2,700m"}},
  {"id":"in_af_palam","name":"Palam Air Force Station (Delhi)","lat":28.560,"lon":77.090,"country":"India","cc":"IN","type":"air_base","arm":"IAF","status":"active","desc":"Delhi, WAC HQ","details":{"role":"Western Air Command HQ","aircraft":["Boeing 737","Embraer"],"runways":"Shared with IGI Airport"}},
  {"id":"in_af_thoise","name":"Thoise Air Force Station","lat":34.630,"lon":77.320,"country":"India","cc":"IN","type":"air_base","arm":"IAF","status":"active","desc":"Siachen operations, highest ALG","details":{"role":"Siachen glacier logistics","aircraft":["An-32","Dhruv"],"runways":"1 × short ALG","notable":"Northernmost IAF base"}},
  {"id":"in_af_hasimara_tejas","name":"Hasimara No.18 Sqn (LCA Tejas)","lat":26.698,"lon":89.350,"country":"India","cc":"IN","type":"air_base","arm":"IAF","status":"active","desc":"Second LCA Tejas squadron base","details":{"role":"Air defense","aircraft":["LCA Tejas Mk1"],"notable":"Flying Bullets squadron"}},
  {"id":"in_af_pune_wac","name":"Maintenance Command HQ (Nagpur)","lat":21.092,"lon":79.047,"country":"India","cc":"IN","type":"air_base","arm":"IAF","status":"active","desc":"IAF Maintenance Command","details":{"role":"Aircraft maintenance, overhaul"}},
  {"id":"in_af_tughlakabad","name":"Tughlakabad AFS (Delhi)","lat":28.503,"lon":77.251,"country":"India","cc":"IN","type":"air_base","arm":"IAF","status":"active","desc":"Delhi area support base","details":{"role":"Communications, logistics"}},
  {"id":"in_af_ojhar","name":"Ojhar Air Force Station (Nasik)","lat":20.120,"lon":73.900,"country":"India","cc":"IN","type":"air_base","arm":"IAF","status":"active","desc":"HAL MiG-29K overhaul facility","details":{"role":"Overhaul and repair","aircraft":["MiG-29K"],"notable":"HAL overhaul division"}},
  {"id":"in_af_arjan_singh","name":"AFS Panagarh (Arjan Singh)","lat":23.473,"lon":87.427,"country":"India","cc":"IN","type":"air_base","arm":"IAF","status":"active","desc":"West Bengal, Eastern Air Command","details":{"role":"Fighter, transport","aircraft":["C-130J","Chinook"],"runways":"1 × 2,700m"}},
  {"id":"in_af_jamnagar2","name":"Jamnagar Naval Air Station","lat":22.469,"lon":70.014,"country":"India","cc":"IN","type":"air_base","arm":"Navy","status":"active","desc":"Naval aviation training","details":{"role":"Naval pilot training"}},
  {"id":"in_af_sirsa","name":"Sirsa Air Force Station","lat":29.561,"lon":75.013,"country":"India","cc":"IN","type":"air_base","arm":"IAF","status":"active","desc":"Haryana, MiG-21 base","details":{"role":"Fighter ops","aircraft":["MiG-21"]}},
  {"id":"in_af_adampur","name":"Adampur Air Force Station","lat":31.433,"lon":75.759,"country":"India","cc":"IN","type":"air_base","arm":"IAF","status":"active","desc":"Punjab, frontline fighter base","details":{"role":"Air defense","aircraft":["Su-30MKI","Jaguar"],"runways":"1 × 2,700m"}},
  {"id":"in_af_maharajpur","name":"Maharajpur AFS (Gwalior)","lat":26.282,"lon":78.225,"country":"India","cc":"IN","type":"air_base","arm":"IAF","status":"active","desc":"Central India, Mirage 2000 wing","details":{"role":"Strike wing"}},
  {"id":"in_af_allahabad","name":"Bamrauli Air Force Station","lat":25.440,"lon":81.734,"country":"India","cc":"IN","type":"air_base","arm":"IAF","status":"active","desc":"UP, training base","details":{"role":"Training","runways":"1 × 2,400m"}},
  {"id":"in_af_hakimpet","name":"Hakimpet Air Force Station","lat":17.543,"lon":78.500,"country":"India","cc":"IN","type":"air_base","arm":"IAF","status":"active","desc":"Hyderabad, helicopter training","details":{"role":"Helicopter training","aircraft":["Chetak","Dhruv","Chinook"]}},
  {"id":"in_af_kalburgi","name":"Kalaburagi Air Force Station","lat":17.418,"lon":76.812,"country":"India","cc":"IN","type":"air_base","arm":"IAF","status":"active","desc":"Karnataka, under expansion","details":{"role":"Forward base","status":"expansion"}},
  {"id":"in_af_bhatinda","name":"Bhatinda Air Force Station","lat":30.201,"lon":74.958,"country":"India","cc":"IN","type":"air_base","arm":"IAF","status":"active","desc":"Punjab, Pakistan border","details":{"role":"Forward fighter ops"}},
  {"id":"in_af_sarsawa","name":"Sarsawa Air Force Station","lat":29.993,"lon":77.434,"country":"India","cc":"IN","type":"air_base","arm":"IAF","status":"active","desc":"UP, helicopter base","details":{"role":"Helicopter ops","aircraft":["Mi-25","Mi-35","Apache AH-64E"],"notable":"Attack helicopter wing"}},
  {"id":"in_af_tezgaon","name":"Tezpur FW Station (No.8 Sqn)","lat":26.717,"lon":92.785,"country":"India","cc":"IN","type":"air_base","arm":"IAF","status":"active","desc":"Su-30MKI Purba Fighters","details":{"role":"Air superiority","aircraft":["Su-30MKI"]}},
  {"id":"in_af_chettinad","name":"Chettinad AFS (Sivaganga)","lat":10.150,"lon":78.800,"country":"India","cc":"IN","type":"air_base","arm":"IAF","status":"active","desc":"Tamil Nadu fighter base","details":{"role":"Fighter ops"}},
  {"id":"in_af_solomon","name":"Kalikunda (No.2 Sqn)","lat":22.340,"lon":87.210,"country":"India","cc":"IN","type":"air_base","arm":"IAF","status":"active","desc":"Jaguar maritime wing","details":{"role":"Maritime strike","aircraft":["Jaguar"]}},
  {"id":"in_af_sukhna","name":"Air Force Station Sukhna","lat":30.840,"lon":76.870,"country":"India","cc":"IN","type":"air_base","arm":"IAF","status":"active","desc":"Near Chandigarh, logistics","details":{"role":"Logistics hub"}},
  {"id":"in_af_challakere","name":"Challakere Military Complex","lat":14.320,"lon":76.650,"country":"India","cc":"IN","type":"research","arm":"DRDO/DAE","status":"construction","desc":"Nuclear/defense research, under construction","details":{"role":"Nuclear research, missile testing","notable":"INS Arihant missile testing suspected"}},
  {"id":"in_af_fukche","name":"Fukche Advanced Landing Ground","lat":32.950,"lon":79.070,"country":"India","cc":"IN","type":"air_base","arm":"IAF","status":"active","desc":"Ladakh forward ALG","details":{"role":"Forward logistics, patrol","runways":"1 × short ALG"}},
  {"id":"in_af_nyoma","name":"Nyoma Advanced Landing Ground","lat":33.047,"lon":77.971,"country":"India","cc":"IN","type":"air_base","arm":"IAF","status":"active","desc":"Ladakh, near China LAC","details":{"role":"Forward fighter ops","notable":"Being upgraded for fighter aircraft"}},

  # ─── INDIA — NAVY (30 facilities) ──────────────────────────────────
  {"id":"in_nv_vizag","name":"INS Visakhapatnam (ENC HQ)","lat":17.723,"lon":83.232,"country":"India","cc":"IN","type":"naval_base","arm":"Navy","status":"active","desc":"Eastern Naval Command HQ, submarine base","details":{"role":"Fleet HQ, submarine ops","ships":["Scorpene SSK","Sindhughosh SSK"],"notable":"Nuclear submarine base"}},
  {"id":"in_nv_mumbai","name":"INS Shikra (WNC Mumbai)","lat":18.899,"lon":72.840,"country":"India","cc":"IN","type":"naval_base","arm":"Navy","status":"active","desc":"Western Naval Command HQ","details":{"role":"Fleet HQ","ships":["INS Vikrant","Kolkata-class DDG"],"notable":"INS Vikrant homeport"}},
  {"id":"in_nv_kochi","name":"INS Venduruthy (SNC Kochi)","lat":9.966,"lon":76.267,"country":"India","cc":"IN","type":"naval_base","arm":"Navy","status":"active","desc":"Southern Naval Command HQ","details":{"role":"Training, fleet ops","ships":["P-8I Poseidon"],"notable":"P-8I ASW base"}},
  {"id":"in_nv_karwar","name":"INS Kadamba (Karwar)","lat":14.814,"lon":74.133,"country":"India","cc":"IN","type":"naval_base","arm":"Navy","status":"construction","desc":"Project Seabird Phase II, expanding","details":{"role":"Major naval base","notable":"Will be India's largest base, carrier + SSN port","area_sq_km":45}},
  {"id":"in_nv_andaman","name":"INS Jarawa (Port Blair)","lat":11.623,"lon":92.727,"country":"India","cc":"IN","type":"naval_base","arm":"Navy","status":"active","desc":"Andaman & Nicobar Command","details":{"role":"Tri-service command","notable":"India's only tri-service command"}},
  {"id":"in_nv_campbell","name":"INS Baaz (Campbell Bay)","lat":7.021,"lon":93.919,"country":"India","cc":"IN","type":"naval_base","arm":"Navy","status":"active","desc":"Southernmost Indian naval station","details":{"role":"Maritime surveillance","notable":"Near Malacca Strait"}},
  {"id":"in_nv_goa","name":"INS Hansa (Goa)","lat":15.383,"lon":73.830,"country":"India","cc":"IN","type":"naval_base","arm":"Navy","status":"active","desc":"Naval aviation hub, MiG-29K","details":{"role":"Naval aviation","aircraft":["MiG-29K","Kamov Ka-31"],"notable":"Naval air station"}},
  {"id":"in_nv_arakkonam","name":"INS Rajali (Arakkonam)","lat":13.074,"lon":79.662,"country":"India","cc":"IN","type":"naval_base","arm":"Navy","status":"active","desc":"Naval air station, P-8I Poseidon","details":{"role":"Maritime patrol","aircraft":["P-8I","Dornier Do-228"]}},
  {"id":"in_nv_dweep","name":"INS Dweeprakshak (Lakshadweep)","lat":10.573,"lon":72.638,"country":"India","cc":"IN","type":"naval_base","arm":"Navy","status":"active","desc":"Lakshadweep naval detachment","details":{"role":"Island defense"}},
  {"id":"in_nv_chilka","name":"INS Chilka","lat":19.721,"lon":85.092,"country":"India","cc":"IN","type":"training","arm":"Navy","status":"active","desc":"Naval sailor training establishment","details":{"role":"Basic training"}},

  # ─── INDIA — NUCLEAR/MISSILE ───────────────────────────────────────
  {"id":"in_nu_barc","name":"Bhabha Atomic Research Centre","lat":19.028,"lon":73.019,"country":"India","cc":"IN","type":"nuclear","arm":"DAE","status":"active","desc":"Primary nuclear research/weapons facility","details":{"role":"Nuclear weapons R&D, Pu production","notable":"Dhruva reactor for weapons-grade Pu"}},
  {"id":"in_nu_tarapur","name":"Tarapur Atomic Power Station","lat":19.834,"lon":72.660,"country":"India","cc":"IN","type":"nuclear","arm":"DAE","status":"active","desc":"BWR nuclear power plant","details":{"role":"Nuclear power generation","notable":"India's first nuclear power station"}},
  {"id":"in_nu_pokhran","name":"Pokhran Nuclear Test Site","lat":26.913,"lon":71.611,"country":"India","cc":"IN","type":"nuclear","arm":"DRDO","status":"active","desc":"Nuclear test site (1974, 1998)","details":{"role":"Nuclear weapons testing","notable":"Smiling Buddha (1974), Shakti (1998)"}},
  {"id":"in_ms_chandipur","name":"Chandipur Integrated Test Range","lat":21.460,"lon":86.927,"country":"India","cc":"IN","type":"missile_test","arm":"DRDO","status":"active","desc":"BrahMos, Agni, Prithvi missile testing","details":{"role":"Missile development and testing","weapons_systems":["BrahMos","Agni-V","Prithvi-II"]}},
  {"id":"in_ms_wheeler","name":"Abdul Kalam Island (Wheeler)","lat":20.755,"lon":87.085,"country":"India","cc":"IN","type":"missile_test","arm":"DRDO","status":"active","desc":"Agni-5 ICBM test range","details":{"role":"ICBM testing","weapons_systems":["Agni-V","K-4 SLBM"],"notable":"Primary ICBM test site"}},
  {"id":"in_ms_sfc","name":"Strategic Forces Command HQ","lat":28.600,"lon":77.200,"country":"India","cc":"IN","type":"military_base","arm":"SFC","status":"active","desc":"Nuclear triad command authority","details":{"role":"Nuclear weapons delivery command","notable":"Controls Agni, K-series missiles"}},

  # ─── INDIA — ARMY COMMANDS ─────────────────────────────────────────
  {"id":"in_ar_northern","name":"Northern Command (Udhampur)","lat":32.930,"lon":75.140,"country":"India","cc":"IN","type":"military_base","arm":"Army","status":"active","desc":"J&K, LoC, LAC operations","details":{"role":"Army Command HQ","personnel_est":300000}},
  {"id":"in_ar_western","name":"Western Command (Chandigarh)","lat":30.740,"lon":76.790,"country":"India","cc":"IN","type":"military_base","arm":"Army","status":"active","desc":"Pakistan border Strike Corps","details":{"role":"Army Command HQ","personnel_est":250000}},
  {"id":"in_ar_eastern","name":"Eastern Command (Kolkata)","lat":22.570,"lon":88.360,"country":"India","cc":"IN","type":"military_base","arm":"Army","status":"active","desc":"China LAC / Myanmar border","details":{"role":"Army Command HQ","personnel_est":200000}},
  {"id":"in_ar_southern","name":"Southern Command (Pune)","lat":18.520,"lon":73.870,"country":"India","cc":"IN","type":"military_base","arm":"Army","status":"active","desc":"Deccan region, strategic reserve","details":{"role":"Army Command HQ","personnel_est":150000}},
  {"id":"in_ar_central","name":"Central Command (Lucknow)","lat":26.850,"lon":80.950,"country":"India","cc":"IN","type":"military_base","arm":"Army","status":"active","desc":"Central India strategic reserve","details":{"role":"Army Command HQ","personnel_est":100000}},
  {"id":"in_ar_galwan","name":"Galwan Valley Forward Post","lat":34.620,"lon":78.240,"country":"India","cc":"IN","type":"military_base","arm":"Army","status":"active","desc":"2020 India-China clash site, fortified","details":{"role":"Forward post","notable":"20 Indian soldiers killed June 2020"}},
  {"id":"in_ar_siachen","name":"Siachen Base Camp","lat":35.000,"lon":77.420,"country":"India","cc":"IN","type":"military_base","arm":"Army","status":"active","desc":"Siachen Glacier ops, highest battlefield","details":{"role":"Glacier operations","notable":"World's highest battlefield"}},
  {"id":"in_ar_pangong","name":"Pangong Lake Positions","lat":33.750,"lon":79.000,"country":"India","cc":"IN","type":"military_base","arm":"Army","status":"active","desc":"India-China standoff 2020, Finger 8","details":{"role":"Forward fortifications"}},
]

# ═══════════════════════════════════════════════════════════════════════
# IMPORT OTHER COUNTRY DATA
# ═══════════════════════════════════════════════════════════════════════
import sys
sys.path.insert(0, DATA_DIR)
from data_china import china_bases
from data_pak_ru_us import pakistan_bases, russia_bases, usa_bases
from data_others import other_bases

bases.extend(china_bases)
bases.extend(pakistan_bases)
bases.extend(russia_bases)
bases.extend(usa_bases)
bases.extend(other_bases)

# ═══════════════════════════════════════════════════════════════════════
# CONFLICTS
# ═══════════════════════════════════════════════════════════════════════
conflicts = [
  {"id":"ukraine_russia","name":"Russia-Ukraine War","status":"active","intensity":"extreme","start_date":"2022-02-24","parties":["Russia","Ukraine"],"description":"Full-scale Russian invasion.","origin_lat":55.756,"origin_lon":37.617,"target_lat":50.450,"target_lon":30.523,"missile_type":"Kalibr/Kh-101/Iskander","daily_strikes":15,"casualties_est":"500,000+","displaced":"8M+","war_status":True},
  {"id":"israel_gaza","name":"Israel-Gaza War","status":"active","intensity":"extreme","start_date":"2023-10-07","parties":["Israel","Hamas"],"description":"Hamas Oct 7 attacks triggered Israeli operations.","origin_lat":31.500,"origin_lon":34.467,"target_lat":31.355,"target_lon":34.309,"missile_type":"Qassam/Iron Dome","daily_strikes":8,"casualties_est":"50,000+","displaced":"1.9M+","war_status":True},
  {"id":"israel_hezbollah","name":"Israel-Hezbollah Conflict","status":"active","intensity":"high","start_date":"2023-10-08","parties":["Israel","Hezbollah"],"description":"Cross-border exchanges, Israeli strikes on Lebanon.","origin_lat":33.270,"origin_lon":35.593,"target_lat":32.950,"target_lon":35.200,"missile_type":"Katyusha/IAF airstrikes","daily_strikes":5,"casualties_est":"5,000+","war_status":True},
  {"id":"houthi_red_sea","name":"Houthi Red Sea Campaign","status":"active","intensity":"high","start_date":"2023-11-19","parties":["Houthis","USA/UK"],"description":"Houthi drone/missile attacks on shipping.","origin_lat":14.797,"origin_lon":42.952,"target_lat":13.000,"target_lon":43.500,"missile_type":"Shahed/Quds-1","daily_strikes":3,"war_status":True},
  {"id":"iran_israel_direct","name":"Iran-Israel Direct Strikes","status":"active","intensity":"critical","start_date":"2024-04-01","parties":["Iran","Israel"],"description":"Iran 300+ drones/missiles at Israel Apr 2024.","origin_lat":32.428,"origin_lon":53.688,"target_lat":31.768,"target_lon":35.214,"missile_type":"Shahab-3/Shahed-136","daily_strikes":1,"war_status":True},
  {"id":"sudan_civil_war","name":"Sudan Civil War","status":"active","intensity":"extreme","start_date":"2023-04-15","parties":["SAF","RSF"],"description":"SAF vs RSF across Sudan.","origin_lat":15.501,"origin_lon":32.560,"target_lat":13.635,"target_lon":25.880,"missile_type":"Artillery","daily_strikes":12,"casualties_est":"20,000+","displaced":"9M+","war_status":True},
  {"id":"myanmar_civil_war","name":"Myanmar Civil War","status":"active","intensity":"high","start_date":"2021-02-01","parties":["SAC","PDFs/EAOs"],"description":"Post-coup resistance vs military junta.","origin_lat":19.763,"origin_lon":96.079,"target_lat":21.959,"target_lon":96.089,"missile_type":"Airstrikes","daily_strikes":5,"casualties_est":"50,000+","war_status":True},
  {"id":"somalia_al_shabaab","name":"Somalia Al-Shabaab Conflict","status":"active","intensity":"high","start_date":"2006-01-01","parties":["Somalia","Al-Shabaab"],"description":"Islamist insurgency.","origin_lat":2.047,"origin_lon":45.318,"target_lat":1.650,"target_lon":44.000,"missile_type":"IEDs/airstrikes","daily_strikes":3,"war_status":True},
  {"id":"drc_m23","name":"DRC M23 Conflict","status":"active","intensity":"high","start_date":"2021-11-01","parties":["DRC","M23/Rwanda"],"description":"M23 rebels seized Goma.","origin_lat":-1.674,"origin_lon":29.226,"target_lat":-1.760,"target_lon":28.330,"missile_type":"Artillery/rockets","daily_strikes":6,"casualties_est":"7,000+","war_status":True},
  {"id":"india_china_lac","name":"India-China LAC Tensions","status":"active","intensity":"medium","start_date":"2020-06-15","parties":["India","China"],"description":"Galwan Valley clash. Ongoing LAC tensions.","origin_lat":34.136,"origin_lon":77.547,"target_lat":35.055,"target_lon":79.984,"missile_type":"None","daily_strikes":0,"war_status":False},
  {"id":"south_china_sea","name":"South China Sea Disputes","status":"active","intensity":"medium","start_date":"2010-01-01","parties":["China","Philippines","Vietnam"],"description":"Chinese coast guard harassment of Philippine vessels.","origin_lat":10.700,"origin_lon":114.500,"target_lat":9.750,"target_lon":118.750,"missile_type":"Water cannons","daily_strikes":0,"war_status":False},
  {"id":"north_korea_provocations","name":"North Korea Missile Provocations","status":"active","intensity":"high","start_date":"2022-01-01","parties":["North Korea","USA/SK/Japan"],"description":"Record DPRK missile launches.","origin_lat":39.660,"origin_lon":124.705,"target_lat":37.567,"target_lon":126.978,"missile_type":"Hwasong-17 ICBM","daily_strikes":0,"war_status":False},
]

# ═══════════════════════════════════════════════════════════════════════
# NUCLEAR SITES
# ═══════════════════════════════════════════════════════════════════════
nuclear_sites = [
  {"id":"us_ne_mm","name":"Minuteman III Fields (NE)","lat":41.125,"lon":-98.350,"country":"USA","warheads_est":150,"type":"ICBM","status":"active","desc":"F.E. Warren AFB silos"},
  {"id":"us_nd_mm","name":"Minuteman III Fields (ND)","lat":46.900,"lon":-101.000,"country":"USA","warheads_est":150,"type":"ICBM","status":"active","desc":"Minot AFB silos"},
  {"id":"us_mt_mm","name":"Minuteman III Fields (MT)","lat":47.500,"lon":-109.500,"country":"USA","warheads_est":150,"type":"ICBM","status":"active","desc":"Malmstrom AFB silos"},
  {"id":"ru_tatischevo","name":"Tatishchevo ICBM Base","lat":51.760,"lon":45.590,"country":"Russia","warheads_est":100,"type":"ICBM","status":"active","desc":"RS-28 Sarmat silos"},
  {"id":"ru_uzhur","name":"Uzhur ICBM Base","lat":55.300,"lon":89.800,"country":"Russia","warheads_est":60,"type":"ICBM","status":"active","desc":"RS-28 Sarmat"},
  {"id":"ru_yoshkar","name":"Yoshkar-Ola Mobile ICBM","lat":56.634,"lon":47.865,"country":"Russia","warheads_est":54,"type":"ICBM_mobile","status":"active","desc":"Topol-M/Yars TELs"},
  {"id":"cn_yumen","name":"Yumen DF-41 Silo Field","lat":40.150,"lon":97.350,"country":"China","warheads_est":120,"type":"ICBM","status":"active","desc":"120+ DF-41 silos"},
  {"id":"cn_hami","name":"Hami DF-41 Silo Field","lat":43.100,"lon":93.400,"country":"China","warheads_est":110,"type":"ICBM","status":"construction","desc":"Under construction"},
  {"id":"cn_ordos","name":"Ordos DF-5 Field","lat":38.900,"lon":107.500,"country":"China","warheads_est":48,"type":"ICBM","status":"active","desc":"DF-5B silos"},
  {"id":"pk_sargodha","name":"Pakistan Stockpile","lat":32.080,"lon":72.650,"country":"Pakistan","warheads_est":170,"type":"tactical/strategic","status":"active","desc":"Est. 160-170 warheads"},
  {"id":"in_stockpile","name":"India Stockpile","lat":12.972,"lon":77.595,"country":"India","warheads_est":172,"type":"strategic","status":"active","desc":"Agni-V warheads est."},
  {"id":"il_dimona","name":"Israel Samson Option","lat":31.003,"lon":35.148,"country":"Israel","warheads_est":90,"type":"strategic","status":"active","desc":"80-90 warheads est."},
  {"id":"kp_storage","name":"DPRK Warheads","lat":40.000,"lon":127.000,"country":"North Korea","warheads_est":50,"type":"tactical","status":"active","desc":"40-50+ warheads"},
  {"id":"ir_breakout","name":"Iran Breakout Capability","lat":33.723,"lon":51.727,"country":"Iran","warheads_est":0,"type":"potential","status":"active","desc":"1-2 week breakout est."},
]

# ═══════════════════════════════════════════════════════════════════════
# SURVEILLANCE
# ═══════════════════════════════════════════════════════════════════════
surveillance = [
  {"country":"China","iso2":"CN","level":"critical","sat_count_est":260,"ground_stations":15,"desc":"YAOGAN-30 SIGINT, Jilin optical","methods":["SAR","OPTICAL","SIGINT","ASAT","CYBER"]},
  {"country":"USA","iso2":"US","level":"critical","sat_count_est":400,"ground_stations":30,"desc":"NRO KH-13, Global Hawk","methods":["SAR","OPTICAL","SIGINT","HUMINT","CYBER"]},
  {"country":"Russia","iso2":"RU","level":"high","sat_count_est":140,"ground_stations":18,"desc":"BARS-M optical, Lotos-S SIGINT","methods":["SAR","OPTICAL","SIGINT","ELINT"]},
  {"country":"India","iso2":"IN","level":"high","sat_count_est":55,"ground_stations":8,"desc":"RISAT-2BR1 SAR, EMISAT SIGINT","methods":["SAR","OPTICAL","SIGINT"]},
  {"country":"Israel","iso2":"IL","level":"critical","sat_count_est":20,"ground_stations":4,"desc":"Ofek-16 optical, TECSAR SAR","methods":["SAR","OPTICAL","SIGINT","HUMINT","CYBER"]},
  {"country":"UK","iso2":"GB","level":"high","sat_count_est":25,"ground_stations":6,"desc":"Skynet-6, GCHQ SIGINT","methods":["SIGINT","OPTICAL","CYBER"]},
  {"country":"France","iso2":"FR","level":"high","sat_count_est":15,"ground_stations":5,"desc":"Helios-2, CERES SIGINT","methods":["OPTICAL","SIGINT"]},
  {"country":"Iran","iso2":"IR","level":"medium","sat_count_est":5,"ground_stations":3,"desc":"Noor-1/2/3 military satellites","methods":["OPTICAL","SIGINT"]},
  {"country":"North Korea","iso2":"KP","level":"medium","sat_count_est":2,"ground_stations":2,"desc":"Malligyong-1 (2023)","methods":["OPTICAL"]},
  {"country":"Japan","iso2":"JP","level":"medium","sat_count_est":12,"ground_stations":5,"desc":"IGS optical/radar","methods":["OPTICAL","SAR"]},
  {"country":"Pakistan","iso2":"PK","level":"low","sat_count_est":3,"ground_stations":2,"desc":"PakSat, ISI HUMINT","methods":["SIGINT","HUMINT"]},
]

war_detection = {
  "active_wars":["ukraine_russia","israel_gaza","israel_hezbollah","houthi_red_sea","iran_israel_direct","sudan_civil_war","myanmar_civil_war","somalia_al_shabaab","drc_m23"],
  "high_tension":["india_china_lac","south_china_sea","north_korea_provocations"],
}

# ═══════════════════════════════════════════════════════════════════════
# WRITE ALL JSON FILES
# ═══════════════════════════════════════════════════════════════════════
with open(os.path.join(DATA_DIR, 'bases.json'), 'w') as f:
    json.dump(bases, f, indent=2)

with open(os.path.join(DATA_DIR, 'conflicts.json'), 'w') as f:
    json.dump(conflicts, f, indent=2)

with open(os.path.join(DATA_DIR, 'nuclear_sites.json'), 'w') as f:
    json.dump(nuclear_sites, f, indent=2)

with open(os.path.join(DATA_DIR, 'surveillance.json'), 'w') as f:
    json.dump(surveillance, f, indent=2)

with open(os.path.join(DATA_DIR, 'war_status.json'), 'w') as f:
    json.dump(war_detection, f, indent=2)

# Count by country
from collections import Counter
cc = Counter(b.get('country','?') for b in bases)
print(f"\n✓ bases.json: {len(bases)} total entries")
for country, count in cc.most_common():
    print(f"  {country}: {count}")
print(f"✓ conflicts.json: {len(conflicts)} entries")
print(f"✓ nuclear_sites.json: {len(nuclear_sites)} entries")
print(f"✓ surveillance.json: {len(surveillance)} entries")
print(f"✓ war_status.json written")
