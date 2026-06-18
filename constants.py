import env_loader  # noqa: F401
import os
import random

"""Shared constants for API headers and site defaults."""

BASE_URL = "https://consular.mfa.gov.cn/VISA/api/cova-service/Visa/Apply/V1"
BASE_STATE_URL = "https://consular.mfa.gov.cn/VISA/api/cova-service/Visa/State/V1"
CHECK_OLD_LIST_BASE_URL = "https://bio.visaforchina.cn/staging-api"
R2_ENDPOINT_URL = os.getenv(
    "R2_ENDPOINT_URL",
    "https://522ae3a4b22b1889539177ef851c51ba.r2.cloudflarestorage.com",
)
R2_ACCESS_KEY_ID = os.getenv("R2_ACCESS_KEY_ID", "")
R2_SECRET_ACCESS_KEY = os.getenv("R2_SECRET_ACCESS_KEY", "")
R2_BUCKET_NAME = os.getenv("R2_BUCKET_NAME", "visa-data")
BASE_FILE_UPLOAD_URL = (
    "https://consular.mfa.gov.cn/VISA/api/cova-service/VaApMaterial/V1"
)
PASSPORT_FILE_FOLDER = "resrouces/data"
DEFAULT_EMBASSY = "3001VNVNMA"
DEFAULT_LANG = "en_US"
OLD_APPLY_STATUS_APPROVED = "审核通过"
OLD_APPLY_ID_FOR_TEST_TOKEN = "2026052752203677110"
LOGIN_API_URL = "https://bio.visaforchina.cn/staging-api/application/online/login"
NORMAL_ACCEPT = "application/json, text/plain, */*"
DEFAULT_VI_LANGUAGE = "vi-VN"
LOGIN_DEFAULT_ORIGIN = "https://bio.visaforchina.cn"

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

SEC_CH_UA = '"Chromium";v="148", "Google Chrome";v="148", "Not/A)Brand";v="99"'

MY_VISA_TYPE = {"L15", "L30", "M", "Q"}

HOTEL_DATA = {
    "UNDER_18": (
        {
            "hotel": [
                "Nanxing_hotel.docx",
            ]
        }
    ),
    "L15": (
        {
            "hotel": [
                # "Nanxing_hotel.docx",
                "L_Magic_Design_hotel.docx",
                "hantao_hotel.docx",
                "Pazhou_Exhibition_Huanzpu_GzuangChau.docx",
            ]
        }
    ),
    "L30": (
        {
            "hotel": [
                "GreenTree_Inn_Beejin.docx",
                "Holiday_Inn_Express_ShangHai.docx",
                "Lanvande_Hotel_GzuangChau.docx",
            ]
        }
    ),
}

CV_DATA = "CV.docx"

ENTRIES_TYPE = {"S": "703001", "D": "703002", "M": "703003"}
SERVICE_VISA_TYPE = {"L": ({"I", "G"}), "M": ({"MT", "MP", "MO"})}
VISA_TYPE_VALUE = {
    "L": {
        "I": ({"visaPurpose": 709001, "visaType": 710001}),
        "G": ({"visaPurpose": 709001, "visaType": 710002}),
    }
}
APPLY_VISA_VALIDITY = {"L": 3}
VISA_TYPE_DAY_VALUE = {"L": ({"15", "30"}), "M": ({"MT", "MP", "MO"})}
SERVICE_TYPE_NORMAL_EXPRESS = {"N": "701001", "E": "701002"}

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
MALE_VIETNAMESE_NAMES = (
    "Nguyen Van An",
    "Le Van Cuong",
    "Hoang Van Em",
    "Dang Van Giang",
    "Do Van Hung",
    "Phan Van Minh",
    "Dinh Van Son",
    "Cao Van Uyen",
    "Ta Van Xuan",
    "Tran Van Bach",
    "Pham Van Dat",
    "Vu Van Khoa",
    "Bui Van Manh",
    "Ngo Van Phuc",
    "Truong Van Sang",
    "Vo Van Tuan",
    "Mai Van Vinh",
    "Chu Van Chinh",
    "Nguyen Van Duc",
    "Le Van Hieu",
    "Hoang Van Long",
    "Dang Van Nam",
    "Do Van Phu",
    "Tran Van Hai",
    "Pham Van Khanh",
    "Ngo Van Tai",
    "Bui Van Thanh",
    "Ly Van Trung",
    "Cao Van Bao",
    "Vu Van Tien",
)

FEMALE_VIETNAMESE_NAMES = (
    "Tran Thi Binh",
    "Pham Thi Dung",
    "Vu Thi Phuong",
    "Bui Thi Hoa",
    "Ngo Thi Lan",
    "Truong Thi Nga",
    "Ly Van Oanh",
    "Vo Thi Quynh",
    "Mai Thi Tam",
    "Luu Thi Van",
    "Chu Thi Yen",
    "Nguyen Thi Anh",
    "Le Thi Cam",
    "Hoang Thi Ha",
    "Dang Thi Linh",
    "Do Thi Ngoc",
    "Phan Thi Quyen",
    "Ly Thi Thu",
    "Dinh Thi Uyen",
    "Cao Thi Xuan",
    "Ta Thi Bich",
    "Tran Thi Giang",
    "Pham Thi Kim",
    "Vu Thi Mai",
    "Bui Thi Oanh",
    "Ngo Thi Thao",
    "Nguyen Thi Huong",
    "Le Thi My",
    "Hoang Thi Nhi",
    "Pham Thi Trang",
)

EDUCATION_DEGREE_TYPE = (("Technical_secondary", "714003", "THPT"),)

EDUCATION_SCHOOL_NAMES = (
    "NGO QUYEN",
    "PHUNG HUNG",
    "TON THAT THUYET",
    "TRAN PHU",
    "LE QUY DON",
    "NGUYEN TRAI",
    "NGUYEN HUE",
    "CHU VAN AN",
    "TRAN HUNG DAO",
    "LE HONG PHONG",
    "PHAN CHAU TRINH",
    "NGUYEN DU",
    "PHAM VAN DONG",
    "VO THI SAU",
    "HA HUY TAP",
    "LUONG THE VINH",
    "TRAN DAI NGHIA",
    "LE LAI",
    "TRAN NHAN TONG",
    "LY THUONG KIET",
    "NGUYEN BINH KHIEM",
    "PHAN BOI CHAU",
    "HUYNH THUC KHANG",
    "NGUYEN TAT THANH",
    "DONG DA",
    "BA TRIEU",
    "QUANG TRUNG",
    "HUNG VUONG",
    "TRUONG CHINH",
    "TO HIEU",
    "PHAM NGU LAO",
    "NGO SI LIEN",
    "PHAN DINH PHUNG",
    "NGUYEN THAI HOC",
    "MAC DINH CHI",
    "LE NGOC HAN",
    "MAU THANH",
    "TAY SON",
    "AN DUONG VUONG",
    "DONG KHOI",
    "THANH CONG",
    "HOANG HOA THAM",
    "DINH TIEN HOANG",
    "LE DAI HANH",
    "TRUNG VUONG",
    "GIA LONG",
    "MINH MANG",
    "THIEU TRI",
    "TU DUC",
    "PHU DONG",
    "VAN LANG",
    "AU LAC",
)

FAMILY_PARENT_RELATION_MOTHER = "727003"
FAMILY_PARENT_RELATION_FATHER = "727002"
FAMILY_FATHER_NOT_APPLY_REMARK = "DA MAT"
FAMILY_DEFAULT_PHONE = "0931773485"
FAMILY_STREET_DISTRICT = "LE CHAN"

TRAVEL_CITY_CODE = "CAN1"
TRAVEL_ARRIVAL_COUNTY = "440112"
TRAVEL_INVITE_PROVINCE = "GD"
TRAVEL_PAY_FOR_SELF = "708001"
TRAVEL_PAY_FOR_OTHER = "708002"
TRAVEL_INVITE_RELATION_HOTEL = "KHACH SAN"
TRAVEL_EMERGENCY_RELATION = "NGUOI THAN"
TRAVEL_INVITE_NAMES = ("Hantao AI Select International Apartment",)

JOB_TYPE = (
    ("Businessperson", "713003"),
    ("Company employee", "713004"),
    ("Entertainer", "713005"),
    ("Industrial/agricultural worker", "713006"),
    ("Student", "713007"),
    ("Member of parliament", "713011"),
    ("Government official", "713012"),
    ("Military personnel", "713013"),
    ("NGO staff", "713014"),
    ("Religious personnel", "713015"),
    ("Media representative", "713016"),
    ("Crew member", "713008"),
    ("Self-employed", "713009"),
    ("Unemployed", "713001"),
    ("Retired", "713010"),
    ("Academic", "713017"),
    ("Other", "713002"),
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
        "THOAI SON",
    ],
    "BAC NINH": ["BAC NINH", "TU SON", "YEN PHONG", "QUE VO", "THUAN THANH", "TIEN DU"],
    "CA MAU": ["CA MAU", "NAM CAN", "DAM DOI", "CAI NUOC", "TRAN VAN THOI", "U MINH"],
    "CAN THO": [
        "NINH KIEU",
        "BINH THUY",
        "CAI RANG",
        "O MON",
        "THOT NOT",
        "PHONG DIEN",
    ],
    "CAO BANG": [
        "CAO BANG",
        "BAO LAC",
        "BAO LAM",
        "HA QUANG",
        "TRUNG KHANH",
        "QUANG HOA",
    ],
    "DA NANG": [
        "HAI CHAU",
        "THANH KHE",
        "SON TRA",
        "NGU HANH SON",
        "LIEN CHIEU",
        "CAM LE",
    ],
    "DAK LAK": [
        "BUON MA THUOT",
        "EA KAR",
        "KRONG ANA",
        "KRONG PAK",
        "M'DRAK",
        "BUON DON",
    ],
    "DIEN BIEN": [
        "DIEN BIEN PHU",
        "MUONG NHE",
        "TUAN GIAO",
        "DIEN BIEN",
        "MUONG CHA",
        "NAM PO",
    ],
    "DONG NAI": [
        "BIEN HOA",
        "LONG KHANH",
        "TRANG BOM",
        "NHON TRACH",
        "VINH CUU",
        "LONG THANH",
    ],
    "DONG THAP": ["CAO LANH", "SA DEC", "HONG NGU", "LAP VO", "THANH BINH", "TAM NONG"],
    "GIA LAI": ["PLEIKU", "AN KHE", "AYUN PA", "CHU SE", "CHU PRONG", "DAK DOA"],
    "HA NOI": ["HOAN KIEM", "BA DINH", "DONG DA", "HA DONG", "CAU GIAY", "THANH TRI"],
    "HA TINH": ["HA TINH", "HONG LINH", "KY ANH", "NGHI XUAN", "CAN LOC", "HUONG SON"],
    "HAI PHONG": ["HONG BANG", "NGO QUYEN", "LE CHAN", "HAI AN", "KIEN AN", "DO SON"],
    "HUNG YEN": ["HUNG YEN", "MY HAO", "VAN LAM", "KHOAI CHAU", "YEN MY", "PHU CU"],
    "HUE": ["PHU XUAN", "THUAN HOA", "HUONG THUY", "HUONG TRA", "PHU VANG", "A LUOI"],
    "KHANH HOA": [
        "NHA TRANG",
        "CAM RANH",
        "NINH HOA",
        "VAN NINH",
        "DIEN KHANH",
        "CAM LAM",
    ],
    "LAI CHAU": [
        "LAI CHAU",
        "MUONG TE",
        "SIN HO",
        "PHONG THO",
        "TAN UYEN",
        "THAN UYEN",
    ],
    "LAM DONG": ["DA LAT", "BAO LOC", "DUC TRONG", "DI LINH", "LAM HA", "DON DUONG"],
    "LANG SON": ["LANG SON", "CAO LOC", "LOC BINH", "BAC SON", "CHI LANG", "HUU LUNG"],
    "LAO CAI": ["LAO CAI", "SA PA", "BAT XAT", "BAO THANG", "BAC HA", "MUONG KHUONG"],
    "NGHE AN": ["VINH", "CUA LO", "DIEN CHAU", "QUYNH LUU", "YEN THANH", "DO LUONG"],
    "NINH BINH": [
        "NINH BINH",
        "TAM DIEP",
        "GIA VIEN",
        "HOA LU",
        "YEN KHANH",
        "KIM SON",
    ],
    "PHU THO": ["VIET TRI", "PHU THO", "LAM THAO", "THANH SON", "DOAN HUNG", "TAN SON"],
    "QUANG NGAI": [
        "QUANG NGAI",
        "DUC PHO",
        "BINH SON",
        "SON TINH",
        "TU NGHIA",
        "LY SON",
    ],
    "QUANG NINH": ["HA LONG", "CAM PHA", "UONG BI", "MONG CAI", "DONG TRIEU", "CO TO"],
    "QUANG TRI": [
        "DONG HA",
        "QUANG TRI",
        "VINH LINH",
        "GIO LINH",
        "HUONG HOA",
        "HAI LANG",
    ],
    "SON LA": ["SON LA", "MOC CHAU", "MAI SON", "YEN CHAU", "BAC YEN", "PHU YEN"],
    "TAY NINH": [
        "TAY NINH",
        "HOA THANH",
        "TRANG BANG",
        "GO DAU",
        "BEN CAU",
        "DUONG MINH CHAU",
    ],
    "THAI NGUYEN": [
        "THAI NGUYEN",
        "SONG CONG",
        "PHO YEN",
        "DAI TU",
        "PHU BINH",
        "VO NHAI",
    ],
    "THANH HOA": [
        "THANH HOA",
        "SAM SON",
        "BIM SON",
        "NGHI SON",
        "HOANG HOA",
        "THO XUAN",
    ],
    "TP HO CHI MINH": [
        "SAI GON",
        "CHO LON",
        "GIA DINH",
        "THU DUC",
        "BINH THANH",
        "GO VAP",
    ],
    "TUYEN QUANG": [
        "TUYEN QUANG",
        "HA GIANG",
        "SON DUONG",
        "YEN SON",
        "BAC QUANG",
        "VI XUYEN",
    ],
    "VINH LONG": [
        "VINH LONG",
        "BINH MINH",
        "TAM BINH",
        "TRA ON",
        "LONG HO",
        "MANG THIT",
    ],
}


ALLOWED_CHINA_VISA_TYPES = {
    "L",
    "M",
    "F",
    "Z",
    "X1",
    "X2",
    "S1",
    "S2",
    "Q1",
    "Q2",
    "C",
    "D",
    "G",
    "R",
}

L_30_HOTEL_INFO = [
    {
        "place_city": "BEIJING",
        "iata_code": "PEK",
        "name": "GreenTree Inn Beijing East Yizhuang District Second Kechuang Street Express Hotel",
        "address": "No.17 Second Kechuang Street, Daxing District, Beijing, Daxing, Beijing, 100023, Trung Quốc",
        "city": "BJ",
        "arrivalCounty": "110115",
        "relationship": "KHACH SAN",
        "districtCounty": "",
        "invitePhoneNumber": "15944417395",
        "inviteProvince": "BJ",
        "documentName": "GreenTree_Inn_Beejin.docx",
        "citySelectedBox": "BJ",
    },
    {
        "place_city": "SHANGHAI",
        "iata_code": "SHA",
        "arrive_id": 2,
        "departure_id": 2,
        "name": "Holiday Inn Express Shanghai Pujiang Lianhang Road, an IHG Hotel",
        "address": "No. 618, Zhuyuan Road, Pujiang Zhen, Minhang District, Minhang, Shanghai, 200233, Trung Quốc",
        "city": "SH",
        "arrivalCounty": "310112",
        "relationship": "KHACH SAN",
        "districtCounty": "",
        "invitePhoneNumber": "12164117988",
        "inviteProvince": "310112",
        "documentName": "Holiday_Inn_Express_ShangHai.docx",
        "citySelectedBox": "SH",
    },
    {
        "place_city": "GUANGZHOU",
        "iata_code": "CAN",
        "name": "Lanvande Hotel Guangzhou Eastxiaonan subway station",
        "address": "No.713 Sorth South Jiang Nan Road Guangzhou, China, Hai Zhu, GuangZhou, 510000, Trung Quốc",
        "city": "CAN1",
        "arrivalCounty": "440105",
        "relationship": "KHACH SAN",
        "districtCounty": "",
        "invitePhoneNumber": "12083931111",
        "inviteProvince": "440105",
        "documentName": "Lanvande_Hotel_GzuangChau.docx",
        "citySelectedBox": "CAN1",
    },
]
L_15_HOTEL_OUTPUT_PATH = "chung\\khach_san"
L_15_TICKET_OUTPUT_PATH = "chung\\ve_may_bay"
L_15_VISA_CENTER_CONFIRMATION_OUTPUT_PATH = "chung\\xac_nhan_tu_trung_tam_visa"

L_15_PASSPORT_EMPTY_PAGES_OUTPUT_PATH = "chung\\2_trang_ho_chieu_trang"
L_15_BANK_STATEMENT_OUTPUT_PATH = "chung\\sao_ke_ngan_hang"
L_15_PREVIOUS_TRAVEL_VISA_PHOTOS_OUTPUT_PATH = (
    "lich_su_xuat_canh\\da_tung_di_nuoc_ngoai\\visa_cac_nuoc_khac_anh_ho_chieu"
)
L_15_PREVIOUS_TRAVEL_CHINA_VISA_PHOTOS_OUTPUT_PATH = (
    "lich_su_xuat_canh\\da_tung_di_nuoc_ngoai\\visa_trung_quoc_cu"
)

L_15_NEVER_TRAVELED_EMPTY_PASSPORT_OUTPUT_PATH = (
    "lich_su_xuat_canh\\chua_tung_di_ho_chieu_trang"
)

L_15_RESIDENCE_DOCUMENT_OUTPUT_PATH = (
    "lich_su_xuat_canh\\chua_tung_di_ho_chieu_trang\\giay_cu_tru"
)

L_15_UNDER_18_DOCUMENTS_OUTPUT_PATH = "duoi_18_tuoi\\giay_to_cho_nguoi_duoi_18"

L_15_AUTHORIZATION_LETTER_OUTPUT_PATH = "duoi_18_tuoi\\giay_uy_quyen"
L_15_TRAVEL_PLAN_OUTPUT_PATH = "lich_trinh_du_lich"
TRAVEL_PLAN_21D="Init_goc.docx"

WEEK_SKIP_BY_TYPE = {"L15": random.randint(4, 6), "L30": random.randint(9, 11)}

UNDER_18_HOTEL_INFO = [
    {
        "place_city": "GUANGZHOU",
        "iata_code": "CAN",
        "name": "Nanxing Hotel (Nanxing Hotel)",
        "address": "5th Floor, No. 158, Heguang Road, Tianhe District, Guangzhou City, Guangdong Province, Tianhe",
        "city": "CAN",
        "arrivalCounty": "440106",
        "relationship": "KHACH SAN",
        "districtCounty": "",
        "invitePhoneNumber": "118928746347",
        "inviteProvince": "GD",
        "documentName": "Nanxing_hotel.docx",
        "citySelectedBox": "CAN1",
    },
]
L_15_HOTEL_INFO = [
    # Pazhou Exhibition
    {
        "place_city": "GUANGZHOU",
        "iata_code": "CAN",
        "name": "L-Magic Design hotel ( L-Magic 设计酒店)",
        "address": "No. 31, Tianhui Building, Jiangnan East Road, Haizhu District, Guangzhou, Guangdong Province, Guangzhou, 123456, Trung Quốc 广东省广州市海珠区江南东路天汇大厦31号, 广州市",
        "city": "CAN",
        "arrivalCounty": "440105",
        "relationship": "KHACH SAN",
        "districtCounty": "",
        "invitePhoneNumber": "118924163387",
        "inviteProvince": "GD",
        "documentName": "L_Magic_Design_hotel.docx",
        "citySelectedBox": "CAN1",
    },
    {
        "place_city": "GUANGZHOU",
        "iata_code": "CAN",
        "name": "Hantao AI Select International Apartment",
        "address": "Room 1018 Zhongdingminghui (Middle Tower), No 76 Feng Le Road, Huangpu District, Guangzhou, Guangdong, China, Huang Pu, Guangzhou, 510799, China",
        "city": "CAN",
        "arrivalCounty": "440112",
        "relationship": "KHACH SAN",
        "districtCounty": "",
        "invitePhoneNumber": "115920187600",
        "inviteProvince": "GD",
        "documentName": "hantao_hotel.docx",
        "citySelectedBox": "CAN1",
    },
    {
        "place_city": "GUANGZHOU",
        "iata_code": "CAN",
        "name": "Pazhou Exhibition",
        "address": " 16th Floor, Reception Room, Huijin International Financial Center, Guangzhou City, Guangdong",
        "city": "CAN",
        "arrivalCounty": "440106",
        "relationship": "KHACH SAN",
        "districtCounty": "",
        "invitePhoneNumber": "113751794679",
        "inviteProvince": "GD",
        "documentName": "Pazhou_Exhibition_Huanzpu_GzuangChau.docx",
        "citySelectedBox": "CAN1",
    },
]

FLIGHT_TEMPLATE = {
    "L15": [
        {
            "name": "VE_MAY_BAY_L15_B_Jet.docx",
            "prefix_flight_text": "CZ",
            "prefix_number": "83",
        },
        {"name": "Ve_VN_Air.docx", "prefix_flight_text": "VN", "prefix_number": "05"},
    ],
    "L30": [
        {
            "name": "VE_MAY_BAY_L15_B_Jet.docx",
            "prefix_flight_text": "CZ",
            "prefix_number": "83",
        },
        {"name": "Ve_VN_Air.docx", "prefix_flight_text": "VN", "prefix_number": "05"},
    ],
}

UPLOAD_FILE_CODE: dict[str, list[dict[str, str]]] = {
    "FLIGHT_TICKET": [
        {"categoryCode": "12025062020000706552852", "materialCode": "mfa-003_1"},
    ],
    "OTHER_MATERIALS": [
        {"categoryCode": "12025062114211484037531", "materialCode": "mfa-044_1"},
        {"categoryCode": "12025062114211484037531", "materialCode": "mfa-044_2"},
        {"categoryCode": "12025062114211484037531", "materialCode": "mfa-044_3"},
        {"categoryCode": "12025062114211484037531", "materialCode": "mfa-044_4"},
        {"categoryCode": "12025062114211484037531", "materialCode": "mfa-044_5"},
    ],
    "BANK_STATEMENT": [
        {"categoryCode": "12025062216413672273869", "materialCode": "mfa-007_1"},
        {"categoryCode": "12025062216413672273869", "materialCode": "mfa-007_2"},
        {"categoryCode": "12025062216413672273869", "materialCode": "mfa-007_3"},
        {"categoryCode": "12025062216413672273869", "materialCode": "mfa-007_4"},
    ],
    "OTHER_COUNTRY_VISAS": [
        {"categoryCode": "2026051411041876690", "materialCode": "mfa-011_1"},
        {"categoryCode": "2026051411041876690", "materialCode": "mfa-011_2"},
        {"categoryCode": "2026051411041876690", "materialCode": "mfa-011_3"},
    ],
    "ITINERARY_IN_CHINA": [
        {"categoryCode": "12025062019595907456262", "materialCode": "mfa-004_1"},
    ],
    "HOTEL_RESERVATION_WITH_PAYMENT": [
        {"categoryCode": "12025063014542307352106", "materialCode": "mfa-002_1"},
        {"categoryCode": "12025063014542307352106", "materialCode": "mfa-002_2"},
        {"categoryCode": "12025063014542307352106", "materialCode": "mfa-002_3"},
    ],
    "UNDER_18": [
        {"categoryCode": "22025062114181968780924", "materialCode": "mfa-039_1"},
        {"categoryCode": "22025062114181968780924", "materialCode": "mfa-039_2"},
        {"categoryCode": "22025062114181968780924", "materialCode": "mfa-039_3"},
        {"categoryCode": "22025062114181968780924", "materialCode": "mfa-039_4"},
        {"categoryCode": "22025062114181968780924", "materialCode": "mfa-039_5"},
    ],
    "PREV_CHINESE_PASSPORT_OR_VISA_FOR_EX_CHINESE": [
        {"categoryCode": "22025062418014204043091", "materialCode": "mfa-036_1"},
        {"categoryCode": "22025062418014204043091", "materialCode": "mfa-036_2"},
        {"categoryCode": "22025062418014204043091", "materialCode": "mfa-036_3"},
        {"categoryCode": "22025062418014204043091", "materialCode": "mfa-036_4"},
    ],
    "PREV_CHINESE_VISA": [
        {"categoryCode": "22025062114131912554297", "materialCode": "mfa-033_1"},
        {"categoryCode": "22025062114131912554297", "materialCode": "mfa-033_2"},
        {"categoryCode": "22025062114131912554297", "materialCode": "mfa-033_3"},
    ],
    "PASSPORT_BLANK_PAGES": [
        {"categoryCode": "22025070216180808782737", "materialCode": "mfa-017_1"},
        {"categoryCode": "22025070216180808782737", "materialCode": "mfa-017_2"},
    ],
    "PROOF_OF_LEGAL_STAY": [
        {"categoryCode": "22025062114095544389381", "materialCode": "mfa-031_1"},
        {"categoryCode": "22025062114095544389381", "materialCode": "mfa-031_2"},
    ],
    "HUKOU_OR_EMPLOYMENT_LETTER": [
        {"categoryCode": "22025062114073725280378", "materialCode": "mfa-030_1"},
    ],
}


UPLOAD_CONFIG = {
    "L15": {
        "PASSPORT_BLANK_PAGES": {
            "folder": L_15_PASSPORT_EMPTY_PAGES_OUTPUT_PATH,
            "limit": 2,
        },
        "BANK_STATEMENT": {
            "folder": L_15_BANK_STATEMENT_OUTPUT_PATH,
            "limit": 2,
        },
        "HUKOU_OR_EMPLOYMENT_LETTER": {
            "folder": L_15_RESIDENCE_DOCUMENT_OUTPUT_PATH,
            "limit": 1,
        },
        "FLIGHT_TICKET": {
            "folder": L_15_TICKET_OUTPUT_PATH,
            "limit": 1,
        },
        "HOTEL_RESERVATION_WITH_PAYMENT": {
            "folder": L_15_HOTEL_OUTPUT_PATH,
            "limit": 1,
        },
        "OTHER_MATERIALS": [
            {
                "folder": L_15_NEVER_TRAVELED_EMPTY_PASSPORT_OUTPUT_PATH,
                "limit": 4,
            },
            {
                "folder": L_15_VISA_CENTER_CONFIRMATION_OUTPUT_PATH,
                "limit": 1,
            },
        ],
        "PREV_CHINESE_VISA": {
            "folder": L_15_PREVIOUS_TRAVEL_CHINA_VISA_PHOTOS_OUTPUT_PATH,
            "limit": 3,
        },
        "UNDER_18": [
            {
                "folder": L_15_UNDER_18_DOCUMENTS_OUTPUT_PATH,
                "limit": 5,
            }
        ],
        "OTHER_COUNTRY_VISAS": [
            {
                "folder": L_15_PREVIOUS_TRAVEL_VISA_PHOTOS_OUTPUT_PATH,
                "limit": 3,
            }
        ],
    },
    "L30": {
        "PASSPORT_BLANK_PAGES": {
            "folder": L_15_PASSPORT_EMPTY_PAGES_OUTPUT_PATH,
            "limit": 2,
        },
        "BANK_STATEMENT": {
            "folder": L_15_BANK_STATEMENT_OUTPUT_PATH,
            "limit": 2,
        },
        "HUKOU_OR_EMPLOYMENT_LETTER": {
            "folder": L_15_RESIDENCE_DOCUMENT_OUTPUT_PATH,
            "limit": 1,
        },
        "FLIGHT_TICKET": {
            "folder": L_15_TICKET_OUTPUT_PATH,
            "limit": 1,
        },
        "HOTEL_RESERVATION_WITH_PAYMENT": {
            "folder": L_15_HOTEL_OUTPUT_PATH,
            "limit": 1,
        },
        "OTHER_MATERIALS": [
            {
                "folder": L_15_NEVER_TRAVELED_EMPTY_PASSPORT_OUTPUT_PATH,
                "limit": 4,
            },
            {
                "folder": L_15_VISA_CENTER_CONFIRMATION_OUTPUT_PATH,
                "limit": 1,
            },
        ],
        "PREV_CHINESE_VISA": {
            "folder": L_15_PREVIOUS_TRAVEL_CHINA_VISA_PHOTOS_OUTPUT_PATH,
            "limit": 3,
        },
        "UNDER_18": [
            {
                "folder": L_15_UNDER_18_DOCUMENTS_OUTPUT_PATH,
                "limit": 5,
            }
        ],
        "OTHER_COUNTRY_VISAS": [
            {
                "folder": L_15_PREVIOUS_TRAVEL_VISA_PHOTOS_OUTPUT_PATH,
                "limit": 3,
            }
        ],
        "ITINERARY_IN_CHINA": [
            # {"categoryCode": "12025062019595907456262", "materialCode": "mfa-004_1"}
            {
                "folder": L_15_TRAVEL_PLAN_OUTPUT_PATH,
                "limit": 1,
            },
        ],
    },
}

UPLOAD_FILE_CODE_BY_VISA_TYPE: dict[str, dict[str, dict[str, list[dict[str, str]]]]] = {
    "L15": {
        "COMMON": {
            "FLIGHT_TICKET": [
                {
                    "categoryCode": "12025062020000706552852",
                    "materialCode": "mfa-003_1",
                },
            ],
            "HOTEL_RESERVATION_WITH_PAYMENT": [
                {
                    "categoryCode": "12025063014542307352106",
                    "materialCode": "mfa-002_1",
                },
                {
                    "categoryCode": "12025063014542307352106",
                    "materialCode": "mfa-002_2",
                },
                {
                    "categoryCode": "12025063014542307352106",
                    "materialCode": "mfa-002_3",
                },
            ],
            "PASSPORT_BLANK_PAGES": [
                {
                    "categoryCode": "22025070216180808782737",
                    "materialCode": "mfa-017_1",
                },
                {
                    "categoryCode": "22025070216180808782737",
                    "materialCode": "mfa-017_2",
                },
            ],
            "BANK_STATEMENT": [
                {
                    "categoryCode": "12025062216413672273869",
                    "materialCode": "mfa-007_1",
                },
                {
                    "categoryCode": "12025062216413672273869",
                    "materialCode": "mfa-007_2",
                },
                {
                    "categoryCode": "12025062216413672273869",
                    "materialCode": "mfa-007_3",
                },
                {
                    "categoryCode": "12025062216413672273869",
                    "materialCode": "mfa-007_4",
                },
            ],
            "HUKOU_OR_EMPLOYMENT_LETTER": [
                {
                    "categoryCode": "22025062114073725280378",
                    "materialCode": "mfa-030_1",
                },
            ],
            "OTHER_MATERIALS": [
                {
                    "categoryCode": "12025062114211484037531",
                    "materialCode": "mfa-044_1",
                },
                {
                    "categoryCode": "12025062114211484037531",
                    "materialCode": "mfa-044_2",
                },
                {
                    "categoryCode": "12025062114211484037531",
                    "materialCode": "mfa-044_3",
                },
                {
                    "categoryCode": "12025062114211484037531",
                    "materialCode": "mfa-044_4",
                },
                {
                    "categoryCode": "12025062114211484037531",
                    "materialCode": "mfa-044_5",
                },
            ],
            "PREV_CHINESE_VISA": [
                {
                    "categoryCode": "22025062114131912554297",
                    "materialCode": "mfa-033_1",
                },
                {
                    "categoryCode": "22025062114131912554297",
                    "materialCode": "mfa-033_2",
                },
            ],
            "UNDER_18": [
                {
                    "categoryCode": "22025062114181968780924",
                    "materialCode": "mfa-039_1",
                },
                {
                    "categoryCode": "22025062114181968780924",
                    "materialCode": "mfa-039_2",
                },
                {
                    "categoryCode": "22025062114181968780924",
                    "materialCode": "mfa-039_3",
                },
                {
                    "categoryCode": "22025062114181968780924",
                    "materialCode": "mfa-039_4",
                },
                {
                    "categoryCode": "22025062114181968780924",
                    "materialCode": "mfa-039_5",
                },
            ],
            "OTHER_COUNTRY_VISAS": [
                {
                    "categoryCode": "12025062114213765489140",
                    "materialCode": "mfa-011_1",
                },
                {
                    "categoryCode": "12025062114213765489140",
                    "materialCode": "mfa-011_2",
                },
                {
                    "categoryCode": "12025062114213765489140",
                    "materialCode": "mfa-011_3",
                },
            ],
        },
    },
    "L30": {
        "COMMON": {
            "FLIGHT_TICKET": [
                {
                    "categoryCode": "12025062020000706552852",
                    "materialCode": "mfa-003_1",
                },
            ],
            "HOTEL_RESERVATION_WITH_PAYMENT": [
                {
                    "categoryCode": "12025063014542307352106",
                    "materialCode": "mfa-002_1",
                },
                {
                    "categoryCode": "12025063014542307352106",
                    "materialCode": "mfa-002_2",
                },
                {
                    "categoryCode": "12025063014542307352106",
                    "materialCode": "mfa-002_3",
                },
            ],
            "PASSPORT_BLANK_PAGES": [
                {
                    "categoryCode": "22025070216180808782737",
                    "materialCode": "mfa-017_1",
                },
                {
                    "categoryCode": "22025070216180808782737",
                    "materialCode": "mfa-017_2",
                },
            ],
            "BANK_STATEMENT": [
                {
                    "categoryCode": "12025062216413672273869",
                    "materialCode": "mfa-007_1",
                },
                {
                    "categoryCode": "12025062216413672273869",
                    "materialCode": "mfa-007_2",
                },
                {
                    "categoryCode": "12025062216413672273869",
                    "materialCode": "mfa-007_3",
                },
                {
                    "categoryCode": "12025062216413672273869",
                    "materialCode": "mfa-007_4",
                },
            ],
            "HUKOU_OR_EMPLOYMENT_LETTER": [
                {
                    "categoryCode": "22025062114073725280378",
                    "materialCode": "mfa-030_1",
                },
            ],
            "OTHER_MATERIALS": [
                {
                    "categoryCode": "12025062114211484037531",
                    "materialCode": "mfa-044_1",
                },
                {
                    "categoryCode": "12025062114211484037531",
                    "materialCode": "mfa-044_2",
                },
                {
                    "categoryCode": "12025062114211484037531",
                    "materialCode": "mfa-044_3",
                },
                {
                    "categoryCode": "12025062114211484037531",
                    "materialCode": "mfa-044_4",
                },
                {
                    "categoryCode": "12025062114211484037531",
                    "materialCode": "mfa-044_5",
                },
            ],
            "PREV_CHINESE_VISA": [
                {
                    "categoryCode": "22025062114131912554297",
                    "materialCode": "mfa-033_1",
                },
                {
                    "categoryCode": "22025062114131912554297",
                    "materialCode": "mfa-033_2",
                },
            ],
            "UNDER_18": [
                {
                    "categoryCode": "22025062114181968780924",
                    "materialCode": "mfa-039_1",
                },
                {
                    "categoryCode": "22025062114181968780924",
                    "materialCode": "mfa-039_2",
                },
                {
                    "categoryCode": "22025062114181968780924",
                    "materialCode": "mfa-039_3",
                },
                {
                    "categoryCode": "22025062114181968780924",
                    "materialCode": "mfa-039_4",
                },
                {
                    "categoryCode": "22025062114181968780924",
                    "materialCode": "mfa-039_5",
                },
            ],
            "OTHER_COUNTRY_VISAS": [
                {
                    "categoryCode": "12025062114213765489140",
                    "materialCode": "mfa-011_1",
                },
                {
                    "categoryCode": "12025062114213765489140",
                    "materialCode": "mfa-011_2",
                },
                {
                    "categoryCode": "12025062114213765489140",
                    "materialCode": "mfa-011_3",
                },
            ],
            "ITINERARY_IN_CHINA": [
                {
                    "categoryCode": "12025062019595907456262",
                    "materialCode": "mfa-004_1",
                },
            ],
        },
    },
}

UNIT_OF_HOTEL = 5870276

GIVEN_MALE_VIETNAMESE_NAMES = (
    "Anh Duy",
    "Bao Long",
    "Chi Bao",
    "Cong Minh",
    "Duc Anh",
    "Duc Huy",
    "Duc Manh",
    "Duc Thang",
    "Gia Huy",
    "Hai Dang",
    "Hoang Anh",
    "Hoang Long",
    "Huu Phuc",
    "Huu Thang",
    "Khac Minh",
    "Le Minh",
    "Manh Cuong",
    "Minh Anh",
    "Minh Duc",
    "Minh Hieu",
    "Minh Hoang",
    "Minh Khang",
    "Minh Quan",
    "Ngoc Anh",
    "Ngoc Minh",
    "Phuc An",
    "Phuc Thinh",
    "Quang Huy",
    "Quang Minh",
    "Quang Vinh",
    "Quoc Anh",
    "Quoc Huy",
    "Quoc Khanh",
    "Quoc Thang",
    "Quoc Trung",
    "Tan Phat",
    "Thanh Dat",
    "Thanh Long",
    "Thien An",
    "Thien Phuc",
    "Thien Tu",
    "Tuan Anh",
    "Tuan Kiet",
    "Tuan Minh",
    "Tuan Vu",
    "Van Duc",
    "Viet Anh",
    "Viet Duc",
    "Viet Hoang",
    "Viet Hung",
    "Viet Khang",
    "Viet Long",
    "Viet Phuc",
    "Viet Quan",
    "Viet Thang",
    "Viet Tuan",
)

SEX_MAP = {
    "1": "M",
    "2": "F",
}

NATIONALITY_MAP = {
    "VNM": "Viet Nam",
}

BASE_HEADERS = {
    "Accept": "application/json, text/plain, */*",
    "Accept-Language": "vi-VN",
    "Origin": "https://bio.visaforchina.cn",
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/148.0.0.0 Safari/537.36"
    ),
}


# Mapping loại hộ chiếu -> mã
PASSPORT_TYPE_CODE = {
    "Ordinary": "707001",
    "Service": "707002",
    "Diplomatic": "707003",
    "Official": "707004",
    "Special": "707005",
    "Other": "707006",
}

# Mapping ký hiệu passport -> loại
PASSPORT_SYMBOL_MAP = {
    "P": "Ordinary",  # Phổ thông
    "S": "Service",  # Công vụ
    "D": "Diplomatic",  # Ngoại giao
    "O": "Official",  # Official / Công vụ
    "SP": "Special",  # Đặc biệt (nếu có)
    "X": "Other",  # Khác / fallback
}

EMERGENCY_RELATION_FATHER = "BO"
EMERGENCY_RELATION_MOTHER = "ME"