DEFAULT_CONFIDENCE_THRESHOLD = 0.20
DEFAULT_GAP_THRESHOLD = 0.03
DEFAULT_EFF_THRESHOLD = 0.38

FIELDS = {
    "Energy": (
        "solar power photovoltaic panel wind turbine renewable electricity "
        "microgrid smart grid battery storage energy storage geothermal "
        "thermal collector heat storage PCM phase change material hydrogen fuel "
        "fuel cell hydropower nuclear power generation tidal energy "
        "distributed control grid stabilization power quality inverter "
        "energy transition decarbonization electrification "
        "energi surya panel surya PLTS tenaga angin PLTB pembangkit listrik terbarukan "
        "grid mikro jaringan cerdas penyimpanan energi baterai panas bumi PLTP "
        "pemanas air PATS kolektor termal penyimpanan panas bahan bakar hidrogen "
        "kendali terdistribusi stabilitas jaringan listrik kualitas daya "
        "sistem tenaga transisi energi PLTA PLTU pembangkitan kelistrikan elektrifikasi kepulauan skala kecil"
    ),

    "Environment": (
        "pollution wastewater soil contamination air quality circular economy "
        "heavy metal adsorption activated carbon hybrid adsorbent waste management "
        "remediation phytoremediation biosorption deforestation marine debris "
        "groundwater ecosystem ecology biodiversity conservation sustainability "
        "carbon emission climate change greenhouse gas global warming carbon footprint "
        "microplastic organic compound water treatment desalination "
        "pencemaran limbah air tanah kontaminasi kualitas udara ekonomi sirkular "
        "logam berat adsorpsi adsorben hibrida karbon aktif pengelolaan sampah "
        "remediasi ekosistem ekologi keanekaragaman hayati konservasi keberlanjutan "
        "emisi karbon perubahan iklim gas rumah kaca pemanasan global jejak karbon "
        "senyawa organik pengolahan air mikroplastik sampah laut AMDAL daur ulang"
    ),

    "Infrastructure": (
        "road railway bridge building construction civil engineering structural engineering "
        "urban planning transportation network public facility dam port airport "
        "station area masterplan feasibility study land use smart city "
        "regional development spatial planning geospatial GIS mapping pavement "
        "address standardization location zone region urban mobility traffic management "
        "jalan kereta api jembatan bangunan konstruksi teknik sipil rekayasa struktural "
        "tata kota perencanaan kota transportasi angkutan umum fasilitas umum bendungan "
        "pelabuhan bandara kawasan stasiun masterplan studi kelayakan tata guna lahan "
        "pengembangan kawasan tata ruang spasial pemetaan GIS kota pintar perkerasan jalan "
        "standardisasi alamat lokasi zona wilayah manajemen lalu lintas mobilitas perkotaan"
    ),

    "Industry": (
        "manufacturing industrial process chemical production fine chemical "
        "Industry 4.0 internet of things IoT robotics automation supply chain logistics "
        "cloud computing architecture software engineering deep learning object detection "
        "machine learning artificial intelligence smart factory enterprise resource planning "
        "quality control metallurgy material engineering chemical synthesis "
        "industri manufaktur proses kimia produksi kimia halus Industri 4.0 "
        "internet untuk segala robotika otomasi rantai pasok logistik pabrik pintar "
        "komputasi awan rekayasa perangkat lunak pembelajaran mesin kecerdasan buatan "
        "deteksi objek kendali mutu metalurgi rekayasa material sintesis kimia "
        "teknologi informasi perangkat keras ERP"
    ),

    "Academic": (
        "social policy governance public administration psychology sociology anthropology "
        "education pedagogy curriculum e-learning economics finance business administration "
        "law communication humanities arts linguistics literature political science "
        "public health healthcare nursing pharmacy medical image clinical diagnosis "
        "early disease detection epidemiology medical research mental health "
        "sosial kebijakan tata kelola administrasi publik psikologi sosiologi antropologi "
        "pendidikan pedagogi kurikulum pembelajaran daring ekonomi keuangan bisnis "
        "hukum komunikasi humaniora seni linguistik sastra ilmu politik "
        "kesehatan masyarakat keperawatan farmasi citra medis diagnosis klinis "
        "deteksi dini penyakit epidemiologi penelitian medis kesehatan mental"
    ),
}

EFFICIENCY_KEYWORDS = [
    "entropy reduction exergy thermodynamic heat loss thermal insulation perlambatan entropi eksergi termodinamika pengurangan rugi panas isolasi termal",

    "circularity waste reduction recovery zero waste biomass utilisation waste valorisation "
    "sirkularitas daur ulang pemulihan material tanpa limbah pemanfaatan limbah biomassa "
    "konversi sampah valorisasi limbah pengolahan limbah ekonomi sirkular "
    "efisiensi bahan baku efisiensi material efisiensi sumber daya",

    "energy efficiency fuel saving specific consumption heat rate thermal efficiency "
    "water efficiency irrigation efficiency agricultural efficiency "
    "peningkatan efisiensi energi penghematan bahan bakar efisiensi termal "
    "konservasi energi efisiensi sistem energi efisiensi proses produksi "
    "efisiensi air efisiensi irigasi efisiensi pertanian "
    "optimalisasi penggunaan air efisiensi sumber daya",

    "improving construction efficiency increasing project efficiency "
    "meningkatkan efisiensi pembangunan meningkatkan efektivitas proyek "
    "mengoptimalkan efisiensi konstruksi efisiensi pelaksanaan proyek "
    "efisiensi waktu pembangunan efisiensi biaya proyek efisiensi pelaksanaan konstruksi "
    "meningkatkan efisiensi produksi meningkatkan produktivitas manufaktur",

    "water saving irrigation efficiency agricultural productivity "
    "smart irrigation precision agriculture water conservation "
    "efisiensi irigasi pertanian cerdas optimalisasi air irigasi "
    "konservasi air pertanian produktivitas pertanian "
    "penghematan air irigasi efisiensi penggunaan air pertanian "
    "peningkatan efisiensi pertanian sistem irigasi efisien "
    "optimalisasi irigasi efisiensi sumber daya air",

    "net zero transition decarbonization carbon neutral green infrastructure "
    "low carbon emission reduction clean energy transition "
    "net zero transisi dekarbonisasi infrastruktur hijau rendah karbon "
    "transisi energi bersih pengurangan emisi karbon "
    "bangunan hijau gedung rendah karbon",

    "grid efficiency distribution efficiency power quality "
    "efisiensi jaringan distribusi efisiensi jaringan listrik "
    "kapasitas hosting pengurangan deviasi tegangan "
    "reduksi rugi daya efisiensi transmisi listrik "
    "peningkatan kapasitas jaringan distribusi tenaga listrik",
]

EFFICIENCY_CUE_WORDS = [
    "efisiensi", "efficiency", "efektivitas", "effectiveness",
    "produktivitas", "productivity", "optimalisasi", "optimization",
    "optimasi", "optimizing", "optimize",
    "net zero", "decarbonization", "dekarbonisasi", "carbon neutral",
    "rendah karbon", "low carbon", "green infrastructure",
    "infrastruktur hijau", "emission reduction", "pengurangan emisi",
    "tegangan", "distribusi", "kapasitas hosting", "rugi daya",
    "transmisi listrik", "jaringan listrik", "power grid",
    "power quality", "grid efficiency",
]
