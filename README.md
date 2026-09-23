# 1) Meme Hate Speech Detector

An end-to-end full-stack AI application for analysing meme images, extracting and validating text, generating image captions, detecting potentially hateful content, categorising detected hate speech, storing analysis history, evaluating model performance with human ground truth, and generating professional PDF reports.


<img width="942" height="440" alt="Screenshot 2026-09-23 060215" src="https://github.com/user-attachments/assets/44139e01-74ae-4c15-9506-e990f16298fc" />
<img width="770" height="399" alt="Screenshot 2026-09-23 060238" src="https://github.com/user-attachments/assets/fcf8f59c-9590-4d8e-95c7-f0225d7d1306" />
<img width="755" height="413" alt="Screenshot 2026-09-23 060247" src="https://github.com/user-attachments/assets/f9a7fdf3-21b0-4943-93d9-92f695e05641" />
<img width="946" height="437" alt="Screenshot 2026-09-23 060326" src="https://github.com/user-attachments/assets/eec2a734-9051-44c4-a0ee-452f86bb028a" />
<img width="957" height="434" alt="Screenshot 2026-09-23 060406" src="https://github.com/user-attachments/assets/0bc4f12a-abae-44e0-88c1-15122e249acf" />
<img width="946" height="438" alt="Screenshot 2026-09-23 060424" src="https://github.com/user-attachments/assets/f756bbf4-5e8d-490a-87bc-9126a5e896ed" />
<img width="938" height="438" alt="Screenshot 2026-09-23 060501" src="https://github.com/user-attachments/assets/0bba316c-9f57-4ec8-bc91-2f7c33597290" />
<img width="954" height="443" alt="Screenshot 2026-09-23 060516" src="https://github.com/user-attachments/assets/afe05f2b-bb18-4b42-8ab9-3cf91f2a858f" />


# 2) Project Overview

The **Meme Hate Speech Detector** combines:

meme-detector/

backend/
  app/
    core/
      dependencies.py
      security.py

    features/
      analyze/
        router.py
        service.py

      auth/
        router.py
        service.py

      export/
        router.py
        service.py

      history/
        router.py
        service.py

      research/
        router.py
        service.py

      serializers.py

    ml/
      ocr_engine.py
      language_validator.py
      caption_engine.py
      classifier_engine.py
      keywords.py
      image_utils.py

    models/
      user.py
      analysis.py

    schemas/
      analysis.py
      auth.py
      export.py

    services/
      indiclid_service.py

    database.py
    config.py
    main.py

  requirements.txt
  Dockerfile

frontend/
  src/
    app/
      core/
      features/
        analyze/
        history/
        research/
        auth/
      shared/
        components/

  angular.json
  package.json

database/
  schema.sql

docker-compose.yml
README.md

### Basic Workflow

Upload Meme → OCR → Language Validation → Image Captioning → Hate Speech Detection → Category Detection → Save Result → History & Research

# 3) The application follows a complete AI analysis pipeline:

Meme Upload
     ↓
OCR Language Selection
     ↓
Image Preprocessing
     ↓
EasyOCR
     ↓
OCR Post-processing
     ↓
Language Validation
     ↓
BLIP Image Caption
     ↓
OCR Text + Caption
     ↓
Hate Speech Classification
     ↓
HATE / SAFE
     ↓
Hate Category
     ↓
Optional Image Blur
     ↓
MySQL Persistence
     ↓
Frontend Result
     ↓
History / Analytics
     ↓
Ground Truth Research
     ↓
Accuracy / Precision / Recall / F1
     ↓
PDF Reports


# 4) Supported OCR Languages

The current application supports:

Code	Language
en	English
hi	Hindi
mr	Marathi

# 5) Only one OCR language is selected for each analysis request.

                  Language validation examples: 

                  Selected OCR Language
                            +
                        OCR Text
                            ↓
                    Script Analysis
                            ↓
                  Language Detection
                            ↓
                  Hindi / Marathi
                  Disambiguation
                            ↓
                  Multiple Evidence Signals
                            ↓
                  ┌─────────┼──────────┐
                  ↓         ↓          ↓
                  Match   Mismatch   Uncertain
                  ↓         ↓          ↓
                  Continue  Error    Safe handling


# 6) The application also handles:

    No readable text
    Uncertain language detection
    Low-confidence OCR
    Difficult meme images


# 7) AI / ML Pipeline : 

                    ┌───────────────┐
                    │  Meme Image   │
                    └───────┬───────┘
                            ↓
                    ┌───────────────┐
                    │ Image         │
                    │ Preprocessing │
                    └───────┬───────┘
                            ↓
                    ┌───────────────┐
                    │    EasyOCR    │
                    └───────┬───────┘
                            ↓
                    ┌───────────────┐
                    │ OCR Post      │
                    │ Processing    │
                    └───────┬───────┘
                            ↓
                    ┌───────────────┐
                    │ Language      │
                    │ Validation    │
                    └───────┬───────┘
                            ↓
                    ┌───────────────┐
                    │ BLIP Caption  │
                    └───────┬───────┘
                            ↓
                 ┌──────────────────────┐
                 │ OCR Text + Caption   │
                 └──────────┬───────────┘
                            ↓
                    ┌───────────────┐
                    │ Hate Speech   │
                    │ Classifier    │
                    └───────┬───────┘
                            ↓
                   ┌────────┴────────┐
                   ↓                 ↓
                HATE               SAFE
                   ↓                 ↓
            Hate Category          None
                   ↓
             Optional Blur
                   ↓
             Save Result
                   ↓
                MySQL

# 8) OCR Pipeline:

          The OCR engine uses EasyOCR together with image preprocessing and text post-processing.

                          Input Image
                              ↓
                          Image Upscaling
                              ↓
                          Original Image OCR
                              ↓
                          CLAHE / Contrast Enhancement
                              ↓
                          Adaptive Threshold OCR
                              ↓
                          Multiple OCR Candidates
                              ↓
                          Confidence Filtering
                              ↓
                          Bounding-box Ordering
                              ↓
                          Duplicate Removal
                              ↓
                          Candidate Scoring
                              ↓
                          Best OCR Result
                              ↓
                          Word-spacing Correction
                              ↓
                          Final OCR Text




# 9) Authentication: The project uses JWT-based authentication.

                Register
                  ↓
                Login
                  ↓
                JWT Access Token
                  ↓
                Angular Local Storage
                  ↓
                HTTP Interceptor
                  ↓
                Authorization: Bearer <token>
                  ↓
                FastAPI
                  ↓
                Current Authenticated User


# 10) Frontend: The Angular frontend provides a user-friendly interface for meme analysis, history tracking, and analytics visualization.

          Frontend technology : 

          | Technology         | Purpose                   |
| ------------------ | ------------------------- |
| Angular 18         | Application framework     |
| TypeScript         | Programming language      |
| HTML               | UI                        |
| SCSS               | Styling                   |
| RxJS               | Reactive programming      |
| Angular HttpClient | Backend API communication |
| Chart.js           | Charts                    |
| ng2-charts         | Angular chart integration |
| jsPDF              | Research PDF generation   |
                           
                           ↓

# 11) Backend: The FastAPI backend handles meme analysis, OCR processing, hate speech classification, and database interactions.

Backend Technology

HTTP / JSON
     ↓
FastAPI Backend
     ↓
Auth | Analyze | History | Research | Export
     ↓
AI / ML
     ↓
EasyOCR
     ↓
Language Validation
     ↓
BLIP
     ↓
Hate Speech Classifier
     ↓
Categorisation
     ↓
Image Processing
                           ↓
# 12) Database: The MySQL database stores analysis results, user data, and history for future reference.

          Database technology : 

          | Technology         | Purpose                   |
          | ------------------ | ------------------------- |
          | MySQL              | Relational database       |

# 13) Model Evaluation : The application evaluates the performance of the hate speech classification model using human-annotated ground truth data.

          Evaluation metrics : 

          | Metric             | Purpose                   |
          | ------------------ | ------------------------- |
          | Accuracy           | Overall correctness       |
          | Precision          | Correct positive predictions |
          | Recall             | True positive rate        |
          | F1 Score           | Balance between precision and recall |
          | Confusion Matrix   | Visual representation of classification results |

# 14) PDF Reporting : The application generates professional PDF reports summarizing analysis results, model performance, and user history.

          PDF reporting technology : 

          | Technology         | Purpose                   |
          | ------------------ | ------------------------- |
          | jsPDF              | PDF generation            |


# 15) Frontend Pages : 

                  1. Analyse Images

                  The main AI analysis page.
                  Features:

                  Upload images
                  Select OCR language
                  Select threshold
                  Batch analysis
                  Loading state
                  Error handling
                  Result cards
                  OCR output
                  Caption
                  Hate/safe result
                  Hate score
                  Safe score
                  Category

                  Current analysis PDF export
                  2. Upload History

                  The history dashboard provides:

                  Total analyses
                  Hateful count
                  Safe count
                  Average hate score
                  All filter
                  Hateful-only filter
                  Safe-only filter
                  Analytics charts
                  Delete individual analysis
                  Clear history
                  Full history PDF export
                  3. Research Metrics

                  The research page provides:

                  Ground truth annotation
                  SAFE/HATE labelling
                  Accuracy
                  Precision
                  Recall
                  F1 Score
                  Confusion Matrix
                  Metric explanations
                  Research Metrics PDF

                  4. Authentication

                  Includes:
                  Registration
                  Login
                  JWT session
                  Protected API requests
                  Logout

# Authentication APIs :

    1. Register
    POST /api/auth/register
    
    2. Login
    POST /api/auth/login
    
    3. Current User
    GET /api/auth/me

    4. Analysis API
    POST /api/analyze/upload

    5. History API
    GET /api/history

    6. Research Metrics API
    GET /api/research/metrics

    7. PDF Report API
    GET /api/research/report
    
    8. Delete Analysis API
    DELETE /api/history/{analysis_id}

    9. Clear History API
    DELETE /api/history/clear

    10. Logout API
    POST /api/auth/logout

    11. Refresh Token API
    POST /api/auth/refresh

    12. Update User API
    PUT /api/auth/update

    13. Get statistics
    GET /api/history/stats

    14. Full History PDF
    GET /api/export/pdf/history

    15. Single Analysis PDF
    GET /api/export/pdf/{analysis_id}


  # 16) Conclusion : The Meme Hate Speech Detector is a comprehensive AI application that combines OCR, image captioning, hate speech classification, and analytics to provide a robust solution for detecting and categorizing potentially hateful content in memes.

  # 17) Future Work : Future enhancements may include support for additional languages, improved hate speech detection models, and integration with social media platforms for real-time meme,video/reels analysis.

  # 18) Contact Us : Email : [yadav.aniket7171@gmail.com]


  ### Features Summary :

  # 17) Future Work

The current Meme Hate Speech Detector provides an end-to-end pipeline for
OCR-based text extraction, language validation, image captioning, hate speech
classification, category detection, history management, research metrics,
and PDF reporting.

Future versions can extend the system with the following capabilities:

###  AI Conversational Assistant

Integrate a conversational AI assistant to help users understand analysis
results in natural language.


### Voice Assistant

A future version can introduce a voice-based interface that allows users to
interact with the system using speech.


###  Multilingual AI Assistant

The assistant could support multiple Indian languages such as:

- English
- Hindi
- Marathi
- Telugu
- Tamil
- Bengali
- Kannada
- Gujarati  .... all Indian languages

This would make the application more accessible to users who prefer regional
languages.

###  Improved Multimodal AI Analysis

Future versions could use more advanced multimodal AI models that jointly
understand:

- Image content
- OCR text
- Meme context
- Visual objects
- Captions
- Text-image relationships

This could improve detection of memes where hateful meaning depends on both
the image and the text.

###  Video and Reels Analysis

The system can be extended from static images to video content.

Possible pipeline:

Video
→ Frame Extraction
→ OCR
→ Speech-to-Text
→ Visual Analysis
→ Hate Speech Detection
→ Category Detection
→ Timestamp-based Results
→ Report

The system could identify the exact timestamp where potentially harmful
content appears.

###  Real-Time Social Media Content Moderation

Future versions could provide integrations with supported social-media or
content-management platforms.

The system could analyse newly uploaded content and provide moderation
assistance before publication.

Possible workflow:

New Content
→ AI Analysis
→ Risk Score
→ Category
→ Human Review
→ Approve / Reject / Escalate

### Real-Time Web Application Notifications

###  Cloud Deployment and Scalability


### Mobile Application

A mobile application could allow users or moderators to:

- Capture a meme using the camera
- Upload images
- Analyse content
- View classification results
- Use voice commands
- Review moderation history
- Receive alerts


###  AI Moderation Copilot

A long-term goal is to transform the application into an AI moderation
copilot.

The copilot could combine:

OCR
+ Image Understanding
+ Hate Speech Classification
+ Language Detection
+ Voice Interaction
+ Conversational AI
+ Human Review
+ Analytics

This would allow the system to assist human moderators rather than relying
only on an automated classification decision......! 
