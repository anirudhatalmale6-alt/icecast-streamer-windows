===================================
   משדר אודיו ל-Icecast
   Icecast Audio Streamer
===================================

הוראות התקנה:
--------------

1. הורד ffmpeg מ: https://www.gyan.dev/ffmpeg/builds/
   (בחר: ffmpeg-release-essentials.zip)

2. חלץ את הקובץ והעתק את ffmpeg.exe לתיקייה של התוכנה
   (הקובץ נמצא בתיקייה bin)

3. הפעל את IcecastStreamer.exe

4. בחר מיקרופון, הזן פרטי שרת ולחץ "התחל שידור"


בניית EXE בעצמך:
-----------------
אם אתה רוצה לבנות את ה-EXE בעצמך:

1. התקן Python 3.8+
2. הפעל build_exe.bat
3. ה-EXE יווצר בתיקיית dist


מבנה התיקייה הנדרש:
-------------------
IcecastStreamer/
├── IcecastStreamer.exe
├── ffmpeg.exe          <-- חובה להעתיק!
└── config.json         (נוצר אוטומטית)


===================================
