from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from reportlab.lib import colors

import os
from PIL import Image
from abc import ABC, abstractmethod


IMG_FORMAT_EXT = ('.png', '.jpg', '.jpeg')


class Font:
    def __init__(self, font_name, font_size):
        self.name = font_name
        self.size = font_size


# TODO: use Enum here?
class FontCollection:
    DEFAULT = Font("Helvetica", 12)
    DEFAULT_BOLD = Font("Helvetica-Bold", 12)
    DEFAULT_H1 = Font("Helvetica-Bold", 20)


class PDFBuilder:
    def __init__(self, output_file):
        self.width_page, self.height_page = letter
        self.canvas = canvas.Canvas(output_file, (self.width_page, self.height_page))

        self.font_default = FontCollection.DEFAULT
        self.current_font = None
        self.current_page = 1

    def transform_y_top(self, y_value):
        return self.height_page - y_value

    def transform_pos_top(self, pos):
        return pos[0], self.transform_y_top(pos[1])

    def get_width_centered_page(self, element_width):
        return self.get_el_centered(self.width_page, element_width)

    @staticmethod
    def get_el_centered(frame_dim, element_dim):
        return (frame_dim - element_dim) // 2

    # TODO: not yet tested
    def use_font(self, font: Font):
        assert self.current_font is not None, "No font has been explicitly set."
        tmp_font = self.current_font

        def __inner(page_constructor):
            def __innerinner(*args, **kwargs):
                self.apply_font(font)
                r = page_constructor(*args, **kwargs)
                self.apply_font(tmp_font)
                return r
            return __innerinner
        return __inner

    def apply_font(self, font: Font):
        self.canvas.setFont(font.name, font.size)
        self.current_font = font

    def apply_default_font(self):
        self.apply_font(self.font_default)

    def string_width_current(self, text):
        assert self.current_font is not None, "No font has been explicitly set."
        return self.canvas.stringWidth(text, self.current_font.name, self.current_font.size)

    def draw_string_width_centered(self, y, text):
        text_width = self.string_width_current(text)
        self.canvas.drawString(self.get_width_centered_page(text_width), y, text)

    def add_page(self, page_constructor, new_page=True, apply_default_font=True):
        r = page_constructor(self.canvas, self)

        if new_page:
            self.next_page(apply_default_font)
            #self.current_font = None # TODO: what is the default font of the canvas? (graphics are reset between pages)

        return r

    def next_page(self, apply_default_font=True):
        self.canvas.showPage()
        self.current_font = None
        self.current_page += 1

        if apply_default_font:
            self.apply_default_font()

    def save(self):
        self.canvas.save()

    @staticmethod
    def add_cover_fields(y_cursor):
        def __inner(c: canvas.Canvas, builder):
            # Draw the labels and create the fields for input
            builder.apply_font(FontCollection.DEFAULT_BOLD)

            fields = {
                "Projekt:": 1,
                "Planung:": 3,
                "AG:":  3,
                "Status:": 1,
                "Erstellt:": 1
            }

            longest_title_width = max(builder.string_width_current(i) for i in fields)

            padding = 10
            frame_width = 400
            field_height = 20

            y_field = y_cursor - field_height - padding

            for field, field_count in fields.items():
                for i in range(field_count):
                    y_string = PDFBuilder.get_el_centered(field_height, builder.current_font.size) + y_field

                    field_text = field if i <= 0 else ""
                    form_field = FormTxtField(
                        text=field_text,
                        x=PDFBuilder.get_el_centered(builder.width_page, frame_width),
                        y=y_string,
                        frame_width=frame_width,
                        min_x_field=longest_title_width
                    )

                    form_field.draw(c, builder)

                    if i < field_count - 1:
                        y_field -= form_field.get_frame().with_padding(0).height
                    else:
                        y_field -= form_field.get_frame().with_padding(10).height

            return y_field - padding
        return __inner

    @staticmethod
    def add_cover_header(y_cursor):
        def __inner(c: canvas.Canvas, builder):
            # Optional: Draw a rectangle around the content to frame the page
            # c.setStrokeColor(colors.black)
            builder.apply_font(FontCollection.DEFAULT_H1)

            padding = 30
            width_header = 400
            height_header = builder.current_font.size * 3
            y_header_rect = y_cursor - height_header - padding

            rect_txt_field = RectTxtField(
                text="Deckblatt",
                x=PDFBuilder.get_el_centered(builder.width_page, width_header),
                y=y_header_rect,
                frame_width=width_header,
                frame_height=height_header
            )
            rect_txt_field.draw(c, builder)

            return y_header_rect - padding

        return __inner

    @staticmethod
    def add_cover_letter(c: canvas.Canvas, builder):
        y_cursor = builder.height_page
        y_cursor = PDFBuilder.add_cover_header(y_cursor)(c, builder)
        y_cursor = PDFBuilder.add_cover_fields(y_cursor)(c, builder)

    @staticmethod
    def add_index(categories):
        def __inner(c: canvas.Canvas, builder):
            y_cursor = builder.height_page

            builder.apply_font(FontCollection.DEFAULT_H1)

            padding = 30
            width_header = 400
            height_header = builder.current_font.size * 3
            x_header = PDFBuilder.get_el_centered(builder.width_page, width_header)
            y_cursor = y_cursor - height_header - padding

            rect_txt_field = RectTxtField(
                text="Inhaltsverzeichnis",
                x=x_header,
                y=y_cursor,
                frame_width=width_header,
                frame_height=height_header
            )
            rect_txt_field.draw(c, builder)

            # Add Index lines
            y_cursor -= 100
            builder.apply_default_font()

            category_first_page = builder.current_page + 1

            for category in categories:
                y_cursor -= (builder.current_font.size + 2)

                text_category = category.name
                length_text_category = builder.string_width_current(text_category)
                text_page = f"Seite: {str(category_first_page).zfill(3)}"
                length_text_page = builder.string_width_current(text_page)
                filler = "."
                length_filler = builder.string_width_current(filler)
                filler_full_length = filler * round((width_header - length_text_category - length_text_page) / length_filler)

                text_padded = text_category + filler_full_length + text_page
                text_width = builder.string_width_current(text_padded)

                x_string = x_header + PDFBuilder.get_el_centered(width_header, text_width)
                c.drawString(x_string, y_cursor, text_padded)
                # Link zu der Seite
                c.linkRect(text_padded, category.name, (x_string, y_cursor, x_string + text_width, y_cursor + builder.current_font.size), relative=False)

                category_first_page += category.get_page_count()
        return __inner


class FormatFrame:
    def __init__(self, x, y, width, height):
        self.x = x
        self.y = y
        self.width = width
        self.height = height

    def with_padding(self, padding):
        return FormatFrame(
            x=self.x - padding,
            y=self.y - padding,
            width=self.width + padding * 2,
            height=self.height + padding * 2
        )


class FormatElement(ABC):
    def __init__(self):
        self.frame = None

    @abstractmethod
    def draw(self, c: canvas.Canvas, builder: PDFBuilder):
        pass

    @abstractmethod
    def get_frame(self):
        pass


class FormTxtField(FormatElement):
    def __init__(self, text, x, y, frame_width, field_height=20, min_x_field=None, text_field_padding=30):
        super().__init__()
        self.text = text

        self.x, self.y = x, y
        self.frame_width = frame_width
        self.min_x_field = min_x_field
        self.field_height = field_height
        self.text_field_padding = text_field_padding

    def get_frame(self):
        return FormatFrame(
            x=self.x,
            y=self.y,
            width=self.frame_width,
            height=self.field_height
        )

    def draw(self, c: canvas.Canvas, builder: PDFBuilder):
        frame = self.get_frame()
        if self.min_x_field is None:
            self.min_x_field = builder.string_width_current(self.text)

        c.drawString(
            frame.x,
            frame.y + PDFBuilder.get_el_centered(frame.height, builder.current_font.size) + 2, #+5 = correction value; fix later
            self.text
        )

        # Create a text field
        c.acroForm.textfield(
            #name=f'{self.text.replace(":", "")}Field',
            tooltip=self.text,
            x=frame.x + self.min_x_field + self.text_field_padding,
            y=frame.y + PDFBuilder.get_el_centered(frame.height, self.field_height),
            width=self.frame_width - self.min_x_field - self.text_field_padding,
            height=self.field_height,
            borderColor=colors.black,
            fillColor=colors.white,
            borderWidth=0,
            textColor=colors.black,
            #forceBorder=True
        )


class RectTxtField(FormatElement):
    def __init__(self, text, x, y, frame_width, frame_height):
        super().__init__()
        self.text = text

        self.x, self.y = x, y
        self.frame_width = frame_width
        self.frame_height = frame_height

    def get_frame(self):
        return FormatFrame(
            x=self.x,
            y=self.y,
            width=self.frame_width,
            height=self.frame_height
        )

    def draw(self, c: canvas.Canvas, builder: PDFBuilder):
        frame = self.get_frame()

        c.rect(
            builder.get_width_centered_page(self.frame_width),
            frame.y,
            self.frame_width, self.frame_height
        )

        # Draw the header lower
        builder.draw_string_width_centered(
            frame.y + PDFBuilder.get_el_centered(self.frame_height, builder.current_font.size) + 2,
            self.text
        )


class PDFImage(FormatElement):
    def __init__(self, path):
        super().__init__()

        self.full_name = os.path.split(path)[-1]
        self.name = ".".join(self.full_name.split(".")[:-1])
        self.ext = self.full_name.split(".")[-1]
        self.img = Image.open(path)
        self.path = path

    def get_format(self, max_width, max_height, margin=0.8, x_offset=0, y_offset=0):
        # Calculate size and position
        scaling_coeff = min(max_height / self.img.height, max_width / self.img.width) * margin
        width, height = self.img.width * scaling_coeff, self.img.height * scaling_coeff

        x = PDFBuilder.get_el_centered(max_width, width)
        y = PDFBuilder.get_el_centered(max_height, height)
        # y_position = height - 150 - ((image_height + 50) * j) # Account for text box?

        return tuple(map(round, (x + x_offset, y + y_offset, width, height)))

    # TODO: implement
    def get_frame(self):
        pass

    def draw(self, c: canvas.Canvas, builder: PDFBuilder):
        pass

    def __str__(self):
        return self.name
