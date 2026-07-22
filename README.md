# De-Dup

**NOTE**:

- This project is being archived!
- After many lessons learnt, and so many restarts of the repo we are moving to a new project: `Simplify`
- The last architectural change from 'file-path' centric to '(object-hash, file-path)' <-- '(object-hash, similarity-vectors)' forced us to re-build from zero rather than updating code.

Follow us in `simplify`

## Goals

- de-dup files and centralize in one place.
- Identify similar pictures, audios, videos, documents
- Generate tags for people in pictures and videos

## Definitions

Duplicates are not only exact binary copies, they could be smaller
versions of the original, color transforms (color to BW), resamples of
audio (48khz to 24khz), etc

## Target

Over 1_000_000 files

- Local files
- 10+ HDD/SSD (from 250GB to 4TB)

File types:

- Images
- Audio
- Video
- Documents (MS Word, PDF, txt, Excel, PowerPoint, etc)
- other
