\
        # detectors.py
        import re
        from typing import Dict, List
        import mimetypes

        PHONE_REGEXES = [
            re.compile(r'(?:\+?\d{1,3}[-.\s]?)?(?:\(?\d{2,4}\)?[-.\s]?)?\d{6,10}'),
            re.compile(r'\b[6-9]\d{9}\b'),
        ]

        CURRENCY_SYMBOLS = r'[\$\€\£\₹\¥]'
        NUMBER_REGEX = re.compile(rf'\b{CURRENCY_SYMBOLS}?\s?\d{{1,3}}(?:[,\s]\d{{3}})*(?:\.\d+)?\b|\b{CURRENCY_SYMBOLS}\d+\b')

        NUM_WORDS = [
            "zero","one","two","three","four","five","six","seven","eight","nine","ten",
            "eleven","twelve","thirteen","fourteen","fifteen","sixteen","seventeen",
            "eighteen","nineteen","twenty","thirty","forty","fifty","sixty","seventy",
            "eighty","ninety","hundred","thousand","lakh","lacs","million","billion","crore"
        ]
        NUM_WORDS_RE = re.compile(r'\\b(' + r'|'.join(re.escape(w) for w in NUM_WORDS) + r')(?:[\\s-](' + r'|'.join(re.escape(w) for w in NUM_WORDS) + r'))*\\b', re.IGNORECASE)

        IMAGE_EXTS = {'.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp', '.tiff', '.svg'}

        def detect_phone_numbers(text: str) -> List[str]:
            found = set()
            for r in PHONE_REGEXES:
                for m in r.findall(text or ""):
                    s = m.strip()
                    digits = re.sub(r'\\D', '', s)
                    if 6 <= len(digits) <= 15:
                        found.add(s)
            return sorted(found)

        def detect_currency_numbers(text: str) -> List[str]:
            return list({m[0] if isinstance(m, tuple) else m for m in NUMBER_REGEX.findall(text or "")})

        def detect_numbers_in_words(text: str) -> List[str]:
            return [m.group(0) for m in NUM_WORDS_RE.finditer(text or "")]

        def analyze_attachments(attachments: List[Dict]) -> Dict:
            total = 0
            image_attached = False
            large = []
            for a in attachments:
                size = a.get("size", 0)
                total += size
                ctype = a.get("content_type") or mimetypes.guess_type(a.get("filename", ""))[0]
                fn = a.get("filename", "unknown")
                if ctype and ctype.startswith("image/"):
                    image_attached = True
                else:
                    ext = (fn and '.' in fn and fn[fn.rfind('.'):].lower()) or ''
                    if ext in IMAGE_EXTS:
                        image_attached = True
                if size >= 5 * 1024 * 1024:
                    large.append(fn)
            return {"total_size": total, "image_attached": image_attached, "large_attachments": large}
