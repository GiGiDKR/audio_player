import time
import flet as ft
import flet.canvas as cv


def convertMillis(millis):
    try:
        millis = float(millis)
    except ValueError:
        return "00:00"

    seconds = int(millis / 1000) % 60
    seconds_str = f"0{seconds}" if seconds < 10 else f"{seconds}"
    minutes = int(millis / (1000 * 60)) % 60
    return f"{minutes}:{seconds_str}"


class VolumeSlider(ft.GestureDetector):
    def __init__(self, audio, on_change_volume):
        super().__init__()
        self.visible = False
        self.audio = audio
        self.previous_volume = 1
        self.content = ft.Container(
            width=100,
            height=5,
            content=cv.Canvas(
                shapes=[
                    cv.Rect(x=0, y=0, height=4, border_radius=3, paint=ft.Paint(color=ft.colors.GREY_500), width=100),
                    cv.Rect(x=0, y=0, height=4, border_radius=3, paint=ft.Paint(color=ft.colors.GREY_900), width=100),
                    cv.Circle(x=100, y=2, radius=6, paint=ft.Paint(color=ft.colors.GREY_900)),
                ]
            )
        )
        self.on_hover = self.change_cursor
        self.on_pan_start = self.change_volume
        self.on_pan_update = self.change_volume
        self.on_change_volume = on_change_volume

    def change_audio_volume(self, volume):
        self.audio.volume = volume

    def change_cursor(self, e: ft.HoverEvent):
        e.control.mouse_cursor = ft.MouseCursor.CLICK
        e.control.update()

    def change_volume(self, e):
        if 0 <= e.local_x <= self.content.width:
            self.change_audio_volume(e.local_x / self.content.width)
            self.content.content.shapes[1].width = e.local_x
            self.content.content.shapes[2].x = e.local_x
            self.on_change_volume()
            self.page.update()

    def mute(self):
        self.previous_volume = self.audio.volume
        self.content.content.shapes[1].width = 0
        self.content.content.shapes[2].x = 0
        self.audio.volume = 0

    def unmute(self):
        self.audio.volume = self.previous_volume
        self.content.content.shapes[1].width = self.content.width * self.audio.volume
        self.content.content.shapes[2].x = self.content.width * self.audio.volume
        print("Unmute")


class Track(ft.GestureDetector):
    def __init__(self, audio, on_change_position):
        super().__init__()
        self.visible = False
        self.content = ft.Container(
            content=cv.Canvas(
                on_resize=self.canvas_resized,
                shapes=[
                    cv.Rect(x=0, y=0, height=5, border_radius=3, paint=ft.Paint(color=ft.colors.GREY_500), width=100),
                    cv.Rect(x=0, y=0, height=5, border_radius=3, paint=ft.Paint(color=ft.colors.GREY_900), width=0),
                ]
            ),
            height=10,
            width=float("inf")
        )
        self.audio = audio
        self.audio_duration = 1
        self.track_width = 100
        self.on_pan_start = self.find_position
        self.on_pan_update = self.find_position
        self.on_hover = self.change_cursor
        self.on_change_position = on_change_position

    def canvas_resized(self, e: cv.CanvasResizeEvent):
        print("On resize:", e.width, e.height)
        self.track_width = e.width
        e.control.shapes[0].width = e.width
        e.control.update()

    def find_position(self, e):
        position = int(self.audio_duration * e.local_x / self.track_width)
        self.content.content.shapes[1].width = max(0, min(e.local_x, self.track_width))
        self.update()
        self.on_change_position(position)

    def change_cursor(self, e: ft.HoverEvent):
        e.control.mouse_cursor = ft.MouseCursor.CLICK
        e.control.update()


class AudioPlayer(ft.Column):
    def __init__(self, url):
        super().__init__(tight=True)
        self.audio1 = ft.Audio(
            src=url,
            autoplay=False,
            volume=1,
            balance=0,
            on_loaded=self.audio_loaded,
            on_duration_changed=self.on_duration_changed,
            on_position_changed=self.change_position,
            on_state_changed=self.state_changed,
            on_seek_complete=lambda _: print("Recherche terminée"),
        )
        self.position = 0
        self.track_canvas = Track(audio=self.audio1, on_change_position=self.seek_position)
        self.play_button = ft.IconButton(icon=ft.icons.PLAY_ARROW, visible=False, on_click=self.play)
        self.pause_button = ft.IconButton(icon=ft.icons.PAUSE, visible=False, on_click=self.pause)
        self.position_duration = ft.Text()
        self.volume_slider = VolumeSlider(audio=self.audio1, on_change_volume=self.check_mute)
        self.volume_icon = ft.IconButton(icon=ft.icons.VOLUME_UP, visible=False, on_click=self.volume_icon_clicked)
        self.controls = [
            self.track_canvas,
            ft.Row(
                alignment=ft.MainAxisAlignment.SPACE_AROUND,
                controls=[
                    self.play_button,
                    self.pause_button,
                    self.position_duration,
                    ft.Row(controls=[self.volume_icon, self.volume_slider])
                ]
            )
        ]

    def did_mount(self):
        self.page.overlay.append(self.audio1)
        self.page.update()

    def will_unmount(self):
        self.page.overlay.remove(self.audio1)
        self.page.update()

    def audio_loaded(self, e):
        time.sleep(0.1)
        self.track_canvas.visible = True
        duration = self.audio1.get_duration()
        self.track_canvas.audio_duration = max(duration, 1)
        self.position_duration.value = f"{convertMillis(0)} / {convertMillis(self.track_canvas.audio_duration)}"
        self.play_button.visible = True
        self.volume_slider.visible = True
        self.volume_icon.visible = True
        self.page.update()

    def on_duration_changed(self, e):
        print("Durée changée:", e.data)
        if e.data:
            self.track_canvas.audio_duration = float(e.data)
        else:
            self.track_canvas.audio_duration = 1
        self.position_duration.value = f"{convertMillis(self.position)} / {convertMillis(self.track_canvas.audio_duration)}"
        self.page.update()

    def play(self, e):
        if self.position != 0:
            self.audio1.resume()
        else:
            self.audio1.play()
        self.play_button.visible = False
        self.pause_button.visible = True
        self.page.update()

    def pause(self, e):
        self.audio1.pause()
        self.play_button.visible = True
        self.pause_button.visible = False
        self.page.update()

    def state_changed(self, e):
        if e.data == "completed":
            self.play_button.visible = True
            self.pause_button.visible = False

    def seek_position(self, position):
        self.audio1.seek(position)
        self.page.update()

    def change_position(self, e):
        self.position = float(e.data) if e.data else 0
        self.position_duration.value = f"{convertMillis(self.position)} / {convertMillis(self.track_canvas.audio_duration)}"
        if self.track_canvas.audio_duration > 0:
            self.track_canvas.content.content.shapes[1].width = (
                    self.position / self.track_canvas.audio_duration * self.track_canvas.track_width
            )
        e.control.page.update()

    def volume_icon_clicked(self, e):
        if e.control.icon == ft.icons.VOLUME_UP:
            e.control.icon = ft.icons.VOLUME_OFF
            self.volume_slider.mute()
        else:
            e.control.icon = ft.icons.VOLUME_UP
            self.volume_slider.unmute()
        e.control.page.update()

    def check_mute(self):
        if int(self.audio1.volume * 100) == 0 and self.volume_icon.icon == ft.icons.VOLUME_UP:
            self.volume_icon.icon = ft.icons.VOLUME_OFF
            self.volume_slider.mute()
            self.volume_icon.update()
        elif int(self.audio1.volume * 100) != 0 and self.volume_icon.icon == ft.icons.VOLUME_OFF:
            self.volume_icon.icon = ft.icons.VOLUME_UP
            self.volume_slider.unmute()
            self.volume_icon.update()


def resultat_selection_fichier(page, e: ft.FilePickerResultEvent):
    if e.files:
        fichier_selectionne = e.files[0]
        url = fichier_selectionne.path
        player = AudioPlayer(url=url)
        page.controls.clear()
        page.add(ft.Container(player, alignment=ft.alignment.center, expand=True))
    page.update()


def main(page: ft.Page):
    page.title = "Lecteur audio Flet avec sélecteur de fichier"
    page.window.width = 390
    page.window.height = 844

    file_picker = ft.FilePicker(on_result=lambda e: resultat_selection_fichier(page, e))
    page.overlay.append(file_picker)

    bouton_selection = ft.ElevatedButton(
        "Choisir un fichier audio",
        on_click=lambda _: file_picker.pick_files(allowed_extensions=["mp3", "wav", "flac", "ogg"])
    )

    page.add(ft.Container(bouton_selection, alignment=ft.alignment.center, expand=True))


if __name__ == "__main__":
    ft.app(target=main)
