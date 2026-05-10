# MP3-Parsing-Project
Parsing for Japanese Study - MP3 Createn
# Japanese Textbook Audiobook Creator

**A practical language-learning tool built through human-AI collaboration**

### Overview
A desktop application that converts a bilingual Japanese textbook PDF into high-quality MP3 audio files. Each sentence is spoken in an optimal learning pattern: **Japanese → English → Japanese (repeat)**, with pauses, making it ideal for listening and shadowing practice.

### Key Features
- Accurate sentence extraction from complex PDF layout
- Japanese-first learning flow (JP → EN → JP)
- Adjustable cooldown to prevent Google TTS rate limiting
- Resume support & sentence range selection
- Clean, meaningful MP3 filenames
- Progress logging with estimated remaining time
- One-click full audiobook generation

### Technical Stack
- **Python 3** + **Tkinter** (GUI)
- **PyPDF2** (PDF text extraction)
- **gTTS** (Google Text-to-Speech)
- **ffmpeg** (audio processing & concatenation)
- Robust regex-based cleaning and filtering

### The Challenge
The textbook has a difficult layout: Japanese text, romaji, and English translations often appear on the same or adjacent lines, with footnote markers (`I²`) and multi-line sentences. Simple splitting approaches failed repeatedly.

### Development Process
This project was developed iteratively in close collaboration with **Grok (xAI)**. Over ~12–15 major versions, we:

- Started with basic PDF extraction
- Progressively refined Japanese vs. Romaji vs. English detection
- Added cleaning for footnote markers
- Implemented resume, range selection, and cooldown logic
- Balanced accuracy vs. usability (final accuracy ~90%+)

**My contributions**: Provided real examples, reported failures with screenshots, defined requirements, and made final decisions on trade-offs.  
**Grok’s contributions**: Suggested architecture, wrote complex regex patterns, implemented features, and rapidly iterated based on feedback.

### What I Learned
- Real-world PDF parsing is far messier than expected
- The importance of iterative development and clear feedback loops
- How to effectively collaborate with AI to solve non-trivial problems
- When "good enough" is the pragmatic choice (accepting minor imperfections instead of chasing perfection)

### Results
Successfully processes **~3,700 sentences** from a full Japanese textbook, turning a time-consuming manual task into an automated, repeatable learning resource.

**Status**: Actively used for daily Japanese listening practice.

---

This version is ready to use. It tells a compelling story, shows technical depth, demonstrates collaboration skills, and highlights learning outcomes — all while remaining concise.

Would you like any adjustments (shorter version, more technical tone, or emphasis on specific aspects)?
