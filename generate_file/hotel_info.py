from docxtpl import DocxTemplate

doc = DocxTemplate("../test/L30_Khach_san.docx")

context = {
    "firs": "6",
}

doc.render(context)
doc.save( "../test/output/L30_Khach_san_done.docx")