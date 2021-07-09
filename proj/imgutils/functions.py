import cv2, os

def crop_qr(img_path, dest_dir):

    try:
        print(f"processing image {img_path}")
        img_name = img_path.rsplit('/', 1)[-1]
        print(img_name)

        # Load imgae, grayscale, Gaussian blur, Otsu's threshold
        print(f"reading image {img_path}")
        image = cv2.imread(img_path)
        original = image.copy()
        print(f"converting to grayscale")
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        print(f"applying Gaussian Blur")
        blur = cv2.GaussianBlur(gray, (9,9), 0)
        print(f"applying Threshold")
        thresh = cv2.threshold(blur, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)[1]

        # Morph close
        kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (5,5))
        close = cv2.morphologyEx(thresh, cv2.MORPH_CLOSE, kernel, iterations=2)

        # Find contours and filter for QR code
        print(f"finding contours")
        cnts = cv2.findContours(close, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        print(f"finding contours")
        cnts = cnts[0] if len(cnts) == 2 else cnts[1]
        cropcount = 0
        for i, c in enumerate(cnts):
            print(f"contour {i}")
            peri = cv2.arcLength(c, True)
            approx = cv2.approxPolyDP(c, 0.04 * peri, True)
            x,y,w,h = cv2.boundingRect(approx)
            area = cv2.contourArea(c)
            ar = w / float(h)

            if len(approx) == 4 and area > 1000 and (ar > .85 and ar < 1.3):
                cropcount += 1

                print(f"QR code possibly detected")
                cv2.rectangle(image, (x, y), (x + w, y + h), (36,255,12), 3)
                ROI = original[y:y+h, x:x+w]

                print("crop directory")
                print(os.path.join(dest_dir, f"crop{cropcount}___{img_name}"))
                cv2.imwrite(
                    os.path.join(dest_dir, f"crop{cropcount}___{img_name}"),
                    ROI
                )

        print(f"{cropcount} possible codes found")
        return cropcount

    except Exception as e:
        print(f"couldnt process image {img_path}")
        print(e)