# أداة اكتشاف الملفات الناقصة في textData
# Missing Files Detection Tool for textData

## الوصف | Description

هذه مجموعة من السكريبتات المكتوبة بـ Python لاكتشاف الملفات الناقصة في مجلد textData. يقوم السكريبت بالبحث عن:

This is a collection of Python scripts to detect missing files in the textData folder. The script searches for:

- **المجلدات الفارغة | Empty folders**: مجلدات لا تحتوي على أي ملفات
- **مجلدات JSON فقط | JSON-only folders**: مجلدات تحتوي على ملفات JSON فقط بدون ملفات المحتوى الرئيسية (.md)

## الملفات المتوفرة | Available Files

1. **`detect_missing_files.py`** - السكريبت الأساسي مع تقرير مفصل
2. **`detect_missing_files_simple.py`** - نسخة مبسطة مع مخرجات أوضح
3. **`README.md`** - هذا الملف

## كيفية الاستخدام | How to Use

### المتطلبات | Requirements
- Python 3.6 أو أحدث
- مجلد textData في نفس مكان السكريبت

### تشغيل السكريبت | Running the Script

```bash
# تشغيل النسخة المبسطة (مستحسن)
python detect_missing_files_simple.py

# أو تشغيل النسخة المفصلة
python detect_missing_files.py
```

## النتائج | Results

### مثال على المخرجات | Sample Output

```
🔍 Scanning textData for missing files...
--------------------------------------------------
❌ Empty: 12- السياحة والآثار\الأنظمة\نظام السياحة
⚠️  JSON-only: path\to\folder
✅ Valid: path\to\valid\folder

==================================================
📊 SUMMARY
==================================================
Empty folders: 102
JSON-only folders: 5
Total problematic folders: 107
```

### التقارير المُنشأة | Generated Reports

1. **`missing_files_report.json`** - تقرير مفصل (من السكريبت الأساسي)
2. **`missing_files_summary.json`** - تقرير مُلخص (من السكريبت المبسط)

## شرح أنواع المشاكل | Problem Types Explained

### 1. المجلدات الفارغة | Empty Folders (❌)
- مجلدات لا تحتوي على أي ملفات أو تحتوي على ملفات النظام فقط (.DS_Store)
- هذه المجلدات تحتاج إلى ملفات المحتوى الرئيسية

### 2. مجلدات JSON فقط | JSON-Only Folders (⚠️)
- مجلدات تحتوي على ملفات .json فقط
- تفتقر إلى ملفات المحتوى الرئيسية مثل .md
- عادة تحتوي على:
  - `.manifest.json`
  - `.ocr_review.json`
  - `.build.log`

### 3. المجلدات الصالحة | Valid Folders (✅)
- مجلدات تحتوي على ملفات .md (المحتوى الرئيسي)
- قد تحتوي أيضاً على ملفات داعمة (.json, .log)

## البنية المتوقعة للملفات | Expected File Structure

كل مجلد في آخر مستوى يجب أن يحتوي على:

Each leaf folder should contain:

```
folder/
├── document-name.md                    # المحتوى الرئيسي | Main content
├── document-name--مواد-001-004.md      # أجزاء إضافية | Additional parts
├── document-name.manifest.json        # معلومات الملف | File metadata
├── document-name.ocr_review.json      # مراجعة OCR | OCR review
└── document-name.build.log            # سجل البناء | Build log
```

## مثال على تقرير JSON | JSON Report Example

```json
{
  "scan_date": "2025-09-07T14:50:21",
  "empty_folders": [
    "12- السياحة والآثار\\الأنظمة\\نظام السياحة"
  ],
  "json_only_folders": [
    {
      "path": "path\\to\\folder",
      "json_files": ["file.ocr_review.json"]
    }
  ],
  "summary": {
    "total_empty_folders": 102,
    "total_json_only_folders": 5,
    "total_problematic_folders": 107
  }
}
```

## استكشاف الأخطاء | Troubleshooting

### خطأ: textData folder not found
- تأكد من وجود مجلد textData في نفس مكان السكريبت
- تأكد من تشغيل السكريبت من المجلد الصحيح

### Permission denied
- تأكد من أن لديك صلاحيات القراءة للمجلدات
- قم بتشغيل السكريبت كمدير إذا لزم الأمر

## تخصيص السكريبت | Customizing the Script

يمكنك تعديل السكريبت لتغيير:
- مسار مجلد textData
- أنواع الملفات المقبولة
- تنسيق التقرير

```python
# تغيير مسار المجلد
textdata_path = "path/to/your/textData"

# تغيير أنواع الملفات المقبولة
accepted_extensions = ['.md', '.txt', '.pdf']
```

---

## الدعم | Support

إذا واجهت أي مشاكل أو كان لديك اقتراحات، يرجى التواصل أو فتح issue.

For any issues or suggestions, please contact or open an issue.