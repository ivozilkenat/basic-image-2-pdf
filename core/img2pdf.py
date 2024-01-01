from reportlab.pdfgen import canvas
import os
import tempfile

from core.pdfBuilder import PDFBuilder, FontCollection, PDFImage, IMG_FORMAT_EXT


# TODO: Bild Reihenfolg numerisch
# - Koordinaten System startet nicht oben links

class IMGCategory:
    def __init__(self, name, path, images):
        self.name = name
        self.path = path
        self.images = images
        self.partition_size = 2

    def get_partitions(self):
        return [self.images[i:i+self.partition_size] for i in range(0, len(self.images), self.partition_size)]

    def get_page_count(self):
        return ((len(self.images) - 1) // self.partition_size) + 1

    def add_to_pdf(self, image_count_finished, image_count_total, update_progress_callback):
        def __inner(c: canvas.Canvas, builder: PDFBuilder):
            page_width, page_height = builder.width_page, builder.height_page

            img_c_total = image_count_total
            img_c_finished = image_count_finished

            # add bookmark
            c.bookmarkPage(self.name)

            for images_for_page in self.get_partitions():

                # Add category header
                height_images = builder.add_page(
                    builder.use_font(FontCollection.DEFAULT_H1)(
                        self.add_category(self.name, page_height)
                    ), new_page=False
                )

                # Add images
                max_width, max_height = page_width, height_images // self.partition_size  # TODO: leave space for category

                for image_count, image in enumerate(images_for_page):

                    self.add_image(image, max_width, max_height, image_count)(c, builder)

                    # Update image progress
                    img_c_finished += 1
                    progress = (img_c_finished/img_c_total * 100)
                    update_progress_callback(progress)
                    print(f"Fortschritt: {img_c_finished}/{img_c_total} ({progress:.2f}%)")#, end="\r", flush=True)

                builder.next_page()
                #return img_c_finished # TODO: REMOVE
            return img_c_finished
        return __inner

    def add_image(self, image, max_width, max_height, image_count):
        def __inner(c: canvas.Canvas, builder: PDFBuilder):
            x_img, y_img, width_img, height_img = image.get_format(
                max_width,
                max_height,
                y_offset=(self.partition_size - image_count - 1) * max_height
            )
            with tempfile.NamedTemporaryFile(delete=False, suffix="." + image.ext, mode="w+b") as temp_file:
                image_resized = image.img.resize((1000, round(1000 * width_img / height_img)))
                image_resized.save(temp_file.name)  # , format=image.ext.upper())
                c.drawImage(temp_file.name, x_img, y_img, width=width_img, height=height_img)

            builder.draw_string_width_centered(y_img - 20, image.name)
        return __inner

    def add_category(self, category, page_height):
        def __inner(c: canvas.Canvas, builder: PDFBuilder):
            margin = 25
            header_height = builder.current_font.size + margin * 2
            height_images = page_height - header_height
            builder.draw_string_width_centered(
                height_images + PDFBuilder.get_el_centered(header_height, builder.current_font.size),
                category
            )
            return height_images
        return  __inner

    def __str__(self):
        return self.name

class IMG2PDF:
    def __init__(self, input_dir, output_file):
        self.input_dir = input_dir
        self.output_file = output_file
        self.builder = PDFBuilder(self.output_file)

    def get_categories(self):
        category_objects = list()

        categories = os.listdir(self.input_dir)
        for category in categories:
            category_path = os.path.join(self.input_dir, category)
            if os.path.isdir(category_path):
                category_objects.append(IMGCategory(
                    name=category,
                    path=category_path,
                    images=[PDFImage(os.path.join(category_path, img)) for img in os.listdir(category_path) if img.endswith(IMG_FORMAT_EXT)]
                ))

        return category_objects

    def create_pdf(self, update_progress_callback):
        print("Starte PDF Generierung")
        image_categories = self.get_categories()

        self.builder.add_page(
            PDFBuilder.add_cover_letter
        )
        print("Deckblatt hinzugefügt")

        self.builder.add_page(
            PDFBuilder.add_index(
                image_categories
            )
        )
        print("Inhaltsverzeichnis hinzugefügt")

        image_count_total = sum(len(c.images) for c in image_categories)
        image_count_finished = 0

        for category in image_categories:
            image_count_finished = self.builder.add_page(
                category.add_to_pdf(image_count_finished, image_count_total, update_progress_callback), new_page=False
            )

        print("PDF speichert ...")
        self.builder.save()
        print("PDF erfolgreich erstellt")

    @staticmethod
    def run_img2pdf(input_dir, output_filename, update_progress_callback):
        # Create the PDF
        img2pdf = IMG2PDF(input_dir, output_filename)
        img2pdf.create_pdf(update_progress_callback)


if __name__ == "__main__":
    IMG2PDF.run_img2pdf("../example_source", "test-out.pdf", lambda x: x)
