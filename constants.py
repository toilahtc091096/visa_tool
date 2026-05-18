"""Shared constants for API headers and site defaults."""

# Embassy / site defaults
DEFAULT_EMBASSY = "3001VNVNMA"
DEFAULT_LANG = "en_US"

# Browser-like headers (match captured Postman/cURL samples)
DEFAULT_EMAIL = "wmtravelvn@gmail.com"
DEFAULT_GUID = "17097129405490"
DEFAULT_UID = "2ff8647bc67a4af8879d7d04d2dd2c1b"
ORIGIN = "https://consular.mfa.gov.cn"
REFERER = "https://consular.mfa.gov.cn/VISA/node"
PLT = "vcenter"

USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/148.0.0.0 Safari/537.36"
)

SEC_CH_UA = (
    '"Chromium";v="148", "Google Chrome";v="148", "Not/A)Brand";v="99"'
)

MY_VISA_TYPE = {"L15", "L30", "M", "Q"}

DOCUMENT_DATA = {
    "L15": ({"hotel": ["L15_1_hotel_GreenTree_Inn.docx","L15_1_hotel_Pazhou_Exhibition.docx"]}),
}

ENTRIES_TYPE = {"S":"703001","D":"703002","M":"703003"}
SERVICE_VISA_TYPE = {
    "L" : ({"I","G"}),
    "M" : ({"MT","MP","MO"})
    }
VISA_TYPE_VALUE = {
    "L": {
        "I" : ({"visaPurpose": 709001, "visaType":710001}), 
        "G" : ({"visaPurpose": 709001, "visaType":710002})
    }
}
APPLY_VISA_VALIDITY = {"L":3}
VISA_TYPE_DAY_VALUE = {
    "L" : ({"15","30"}),
    "M" : ({"MT","MP","MO"})
    }
    # entries_type = "S"
    # service_type = "I"
SERVICE_TYPE_NORMAL_EXPRESS = {"N":"701001","E":"701002"}

VIETNAMESE_NAMES = (
    "Nguyen Van An",
    "Tran Thi Binh",
    "Le Van Cuong",
    "Pham Thi Dung",
    "Hoang Van Em",
    "Vu Thi Phuong",
    "Dang Van Giang",
    "Bui Thi Hoa",
    "Do Van Hung",
    "Ngo Thi Lan",
    "Phan Van Minh",
    "Truong Thi Nga",
    "Ly Van Oanh",
    "Vo Thi Quynh",
    "Dinh Van Son",
    "Mai Thi Tam",
    "Cao Van Uyen",
    "Luu Thi Van",
    "Ta Van Xuan",
    "Chu Thi Yen",
    "Nguyen Thi Anh",
    "Tran Van Bach",
    "Le Thi Cam",
    "Pham Van Dat",
    "Hoang Thi Ha",
    "Vu Van Khoa",
    "Dang Thi Linh",
    "Bui Van Manh",
    "Do Thi Ngoc",
    "Ngo Van Phuc",
    "Phan Thi Quyen",
    "Truong Van Sang",
    "Ly Thi Thu",
    "Vo Van Tuan",
    "Dinh Thi Uyen",
    "Mai Van Vinh",
    "Cao Thi Xuan",
    "Luu Van Yen",
    "Ta Thi Bich",
    "Chu Van Chinh",
    "Nguyen Van Duc",
    "Tran Thi Giang",
    "Le Van Hieu",
    "Pham Thi Kim",
    "Hoang Van Long",
    "Vu Thi Mai",
    "Dang Van Nam",
    "Bui Thi Oanh",
    "Do Van Phu",
    "Ngo Thi Thao",
)
 
# (label, highestDegree code, specialty text)
EDUCATION_DEGREE_TYPE = (
    ("Technical_secondary", "714003", "THPT"),
)

# School name middle part: "THPT {name}, {province}" (see SaveEducationInfo cURL)
EDUCATION_SCHOOL_NAMES = (
    "NGO QUYEN",
)

FAMILY_PARENT_RELATION_MOTHER = "727003"
#todo: phan nay co the check them 
FAMILY_FATHER_NOT_APPLY_REMARK = "DA MAT"
FAMILY_DEFAULT_PHONE = "0931773485"
FAMILY_STREET_DISTRICT = "LE CHAN"

TRAVEL_CITY_CODE = "CAN1"
TRAVEL_ARRIVAL_COUNTY = "440112"
TRAVEL_INVITE_PROVINCE = "GD"
TRAVEL_PAY_FOR_SELF = "708001"
TRAVEL_INVITE_RELATION_HOTEL = "KHACH SAN"
TRAVEL_EMERGENCY_RELATION = "BAN BE"
TRAVEL_INVITE_NAMES = (
    "Hantao AI Select International Apartment",
)

JOB_TYPE = (
    ("Businessperson","713003"),
    ("Company employee","713004"),
    ("Entertainer","713005"),
    ("Industrial/agricultural worker","713006"),
    ("Student","713007"),
    ("Member of parliament","713011"),
    ("Government official","713012"),
    ("Military personnel","713013"),
    ("NGO staff","713014"),
    ("Religious personnel","713015"),
    ("Media representative","713016"),
    ("Crew member","713008"),
    ("Self-employed","713009"),
    ("Unemployed","713001"),
    ("Retired","713010"),
    ("Academic","713017"),
    ("Other","713002"),
)

PREFER_JOB_TYPE = (
    "Self-employed",
    "Businessperson",
    "Unemployed",
)

JOB_TYPE_BY_LABEL = dict(JOB_TYPE)
SELF_EMPLOYED_JOB_DESC = "TU KINH DOANH"

VIETNAM_ADMIN = {
    "AN GIANG": [
        "LONG XUYEN",
        "CHAU DOC",
        "TAN CHAU",
        "AN PHU",
        "CHO MOI",
        "THOAI SON"
    ],

    "BAC NINH": [
        "BAC NINH",
        "TU SON",
        "YEN PHONG",
        "QUE VO",
        "THUAN THANH",
        "TIEN DU"
    ],

    "CA MAU": [
        "CA MAU",
        "NAM CAN",
        "DAM DOI",
        "CAI NUOC",
        "TRAN VAN THOI",
        "U MINH"
    ],

    "CAN THO": [
        "NINH KIEU",
        "BINH THUY",
        "CAI RANG",
        "O MON",
        "THOT NOT",
        "PHONG DIEN"
    ],

    "CAO BANG": [
        "CAO BANG",
        "BAO LAC",
        "BAO LAM",
        "HA QUANG",
        "TRUNG KHANH",
        "QUANG HOA"
    ],

    "DA NANG": [
        "HAI CHAU",
        "THANH KHE",
        "SON TRA",
        "NGU HANH SON",
        "LIEN CHIEU",
        "CAM LE"
    ],

    "DAK LAK": [
        "BUON MA THUOT",
        "EA KAR",
        "KRONG ANA",
        "KRONG PAK",
        "M'DRAK",
        "BUON DON"
    ],

    "DIEN BIEN": [
        "DIEN BIEN PHU",
        "MUONG NHE",
        "TUAN GIAO",
        "DIEN BIEN",
        "MUONG CHA",
        "NAM PO"
    ],

    "DONG NAI": [
        "BIEN HOA",
        "LONG KHANH",
        "TRANG BOM",
        "NHON TRACH",
        "VINH CUU",
        "LONG THANH"
    ],

    "DONG THAP": [
        "CAO LANH",
        "SA DEC",
        "HONG NGU",
        "LAP VO",
        "THANH BINH",
        "TAM NONG"
    ],

    "GIA LAI": [
        "PLEIKU",
        "AN KHE",
        "AYUN PA",
        "CHU SE",
        "CHU PRONG",
        "DAK DOA"
    ],

    "HA NOI": [
        "HOAN KIEM",
        "BA DINH",
        "DONG DA",
        "HA DONG",
        "CAU GIAY",
        "THANH TRI"
    ],

    "HA TINH": [
        "HA TINH",
        "HONG LINH",
        "KY ANH",
        "NGHI XUAN",
        "CAN LOC",
        "HUONG SON"
    ],

    "HAI PHONG": [
        "HONG BANG",
        "NGO QUYEN",
        "LE CHAN",
        "HAI AN",
        "KIEN AN",
        "DO SON"
    ],

    "HUNG YEN": [
        "HUNG YEN",
        "MY HAO",
        "VAN LAM",
        "KHOAI CHAU",
        "YEN MY",
        "PHU CU"
    ],

    "HUE": [
        "PHU XUAN",
        "THUAN HOA",
        "HUONG THUY",
        "HUONG TRA",
        "PHU VANG",
        "A LUOI"
    ],

    "KHANH HOA": [
        "NHA TRANG",
        "CAM RANH",
        "NINH HOA",
        "VAN NINH",
        "DIEN KHANH",
        "CAM LAM"
    ],

    "LAI CHAU": [
        "LAI CHAU",
        "MUONG TE",
        "SIN HO",
        "PHONG THO",
        "TAN UYEN",
        "THAN UYEN"
    ],

    "LAM DONG": [
        "DA LAT",
        "BAO LOC",
        "DUC TRONG",
        "DI LINH",
        "LAM HA",
        "DON DUONG"
    ],

    "LANG SON": [
        "LANG SON",
        "CAO LOC",
        "LOC BINH",
        "BAC SON",
        "CHI LANG",
        "HUU LUNG"
    ],

    "LAO CAI": [
        "LAO CAI",
        "SA PA",
        "BAT XAT",
        "BAO THANG",
        "BAC HA",
        "MUONG KHUONG"
    ],

    "NGHE AN": [
        "VINH",
        "CUA LO",
        "DIEN CHAU",
        "QUYNH LUU",
        "YEN THANH",
        "DO LUONG"
    ],

    "NINH BINH": [
        "NINH BINH",
        "TAM DIEP",
        "GIA VIEN",
        "HOA LU",
        "YEN KHANH",
        "KIM SON"
    ],

    "PHU THO": [
        "VIET TRI",
        "PHU THO",
        "LAM THAO",
        "THANH SON",
        "DOAN HUNG",
        "TAN SON"
    ],

    "QUANG NGAI": [
        "QUANG NGAI",
        "DUC PHO",
        "BINH SON",
        "SON TINH",
        "TU NGHIA",
        "LY SON"
    ],

    "QUANG NINH": [
        "HA LONG",
        "CAM PHA",
        "UONG BI",
        "MONG CAI",
        "DONG TRIEU",
        "CO TO"
    ],

    "QUANG TRI": [
        "DONG HA",
        "QUANG TRI",
        "VINH LINH",
        "GIO LINH",
        "HUONG HOA",
        "HAI LANG"
    ],

    "SON LA": [
        "SON LA",
        "MOC CHAU",
        "MAI SON",
        "YEN CHAU",
        "BAC YEN",
        "PHU YEN"
    ],

    "TAY NINH": [
        "TAY NINH",
        "HOA THANH",
        "TRANG BANG",
        "GO DAU",
        "BEN CAU",
        "DUONG MINH CHAU"
    ],

    "THAI NGUYEN": [
        "THAI NGUYEN",
        "SONG CONG",
        "PHO YEN",
        "DAI TU",
        "PHU BINH",
        "VO NHAI"
    ],

    "THANH HOA": [
        "THANH HOA",
        "SAM SON",
        "BIM SON",
        "NGHI SON",
        "HOANG HOA",
        "THO XUAN"
    ],

    "TP HO CHI MINH": [
        "SAI GON",
        "CHO LON",
        "GIA DINH",
        "THU DUC",
        "BINH THANH",
        "GO VAP"
    ],

    "TUYEN QUANG": [
        "TUYEN QUANG",
        "HA GIANG",
        "SON DUONG",
        "YEN SON",
        "BAC QUANG",
        "VI XUYEN"
    ],

    "VINH LONG": [
        "VINH LONG",
        "BINH MINH",
        "TAM BINH",
        "TRA ON",
        "LONG HO",
        "MANG THIT"
    ]
}
