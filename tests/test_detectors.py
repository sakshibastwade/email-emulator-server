\
        from detectors import detect_phone_numbers, detect_currency_numbers, detect_numbers_in_words, analyze_attachments

        def test_phone_detection():
            s = "Call me at +91 9876543210 or 080-1234567"
            phones = detect_phone_numbers(s)
            assert any("9876543210" in p.replace(" ", "") for p in phones)

        def test_currency_detection():
            s = "The amount is ₹1,23,456.78 and $200"
            money = detect_currency_numbers(s)
            assert any("₹" in m or "$" in m for m in money)

        def test_numbers_in_words():
            s = "We transferred five lakh rupees and two million dollars"
            words = detect_numbers_in_words(s)
            assert "five lakh" in " ".join(words).lower()

        def test_attachments():
            atts = [{"filename":"image.jpg","content_type":"image/jpeg","size":1024},
                    {"filename":"doc.pdf","content_type":"application/pdf","size":6*1024*1024}]
            res = analyze_attachments(atts)
            assert res["image_attached"] is True
            assert "doc.pdf" in res["large_attachments"]
