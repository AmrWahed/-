from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.textinput import TextInput
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.spinner import Spinner
from kivy.uix.checkbox import CheckBox
from kivy.uix.progressbar import ProgressBar
from kivy.uix.popup import Popup
from kivy.uix.gridlayout import GridLayout
from kivy.clock import Clock
from kivy.properties import StringProperty, NumericProperty, BooleanProperty, ListProperty
from kivy.lang import Builder
from kivy.logger import Logger
from kivy.core.window import Window
import webbrowser
import json
import os
import re
from urllib.parse import quote
from datetime import datetime

# ======================== UI Design (KV) ========================
KV = '''
<WhatsAppSender>:
    orientation: 'vertical'
    padding: 15
    spacing: 10
    canvas.before:
        Color:
            rgba: 0.94, 0.95, 0.98, 1
        Rectangle:
            pos: self.pos
            size: self.size

    Label:
        text: "WhatsApp Bulk Sender"
        font_size: 24
        bold: True
        color: 0.1, 0.3, 0.6, 1
        size_hint_y: None
        height: 45

    # Numbers
    Label:
        text: "Phone Numbers (one per line)"
        size_hint_y: None
        height: 25
        halign: "left"
        color: 0.2, 0.2, 0.2, 1
    TextInput:
        id: numbers_input
        hint_text: "e.g. 201096576058"
        multiline: True
        size_hint_y: 0.15
        disabled: root.running
        on_text: root.on_data_change()
        background_color: 1, 1, 1, 1
        foreground_color: 0, 0, 0, 1

    # Names
    Label:
        text: "Names (one per line, matches above order)"
        size_hint_y: None
        height: 25
        halign: "left"
        color: 0.2, 0.2, 0.2, 1
    TextInput:
        id: names_input
        hint_text: "e.g. Ahmed"
        multiline: True
        size_hint_y: 0.15
        disabled: root.running
        on_text: root.on_data_change()
        background_color: 1, 1, 1, 1
        foreground_color: 0, 0, 0, 1

    # Addresses
    Label:
        text: "Addresses (one per line, matches above order)"
        size_hint_y: None
        height: 25
        halign: "left"
        color: 0.2, 0.2, 0.2, 1
    TextInput:
        id: addresses_input
        hint_text: "e.g. Maadi, Cairo"
        multiline: True
        size_hint_y: 0.15
        disabled: root.running
        on_text: root.on_data_change()
        background_color: 1, 1, 1, 1
        foreground_color: 0, 0, 0, 1

    # Template section
    BoxLayout:
        size_hint_y: None
        height: 40
        spacing: 8
        Spinner:
            id: template_spinner
            text: "Select Template"
            values: root.template_options
            on_text: root.on_template_select(self.text)
            size_hint_x: 0.5
            background_color: 0.9, 0.9, 0.9, 1
        Button:
            text: "New"
            on_press: root.new_template()
            size_hint_x: 0.25
            background_color: 0.2, 0.6, 0.8, 1
            color: 1, 1, 1, 1
        Button:
            text: "Delete"
            on_press: root.delete_template()
            size_hint_x: 0.25
            background_color: 0.8, 0.2, 0.2, 1
            color: 1, 1, 1, 1

    TextInput:
        id: template_edit
        hint_text: "Message template (use {name} and {address} placeholders)"
        multiline: True
        size_hint_y: 0.12
        disabled: root.running or root.current_template_index < 0
        background_color: 1, 1, 1, 1
        foreground_color: 0, 0, 0, 1

    BoxLayout:
        size_hint_y: None
        height: 40
        Button:
            text: "Save Template"
            on_press: root.save_current_template()
            background_color: 0.3, 0.7, 0.3, 1
            color: 1, 1, 1, 1
        Button:
            text: "Load Templates"
            on_press: root.load_templates()
            background_color: 0.5, 0.5, 0.7, 1
            color: 1, 1, 1, 1

    # Rotate templates
    BoxLayout:
        size_hint_y: None
        height: 40
        CheckBox:
            id: rotate_checkbox
            active: root.rotate_templates
            on_active: root.rotate_templates = self.active
            size_hint_x: None
            width: 40
        Label:
            text: "Rotate Templates (use different template each time)"
            size_hint_x: 1
            color: 0.1, 0.1, 0.1, 1

    # Campaign management
    BoxLayout:
        size_hint_y: None
        height: 40
        spacing: 8
        Label:
            text: "Campaign Name:"
            size_hint_x: None
            width: 110
            color: 0.2, 0.2, 0.2, 1
        TextInput:
            id: campaign_name_input
            hint_text: "Enter campaign name"
            multiline: False
            size_hint_x: 0.4
            background_color: 1, 1, 1, 1
            foreground_color: 0, 0, 0, 1
        Spinner:
            id: campaign_spinner
            text: "Load Campaign"
            values: root.campaign_list
            size_hint_x: 0.3
        Button:
            text: "Delete"
            on_press: root.delete_campaign()
            size_hint_x: 0.15
            background_color: 0.8, 0.3, 0.3, 1
            color: 1, 1, 1, 1

    BoxLayout:
        size_hint_y: None
        height: 40
        Button:
            text: "Save Campaign"
            on_press: root.save_campaign()
            background_color: 0.2, 0.6, 0.8, 1
            color: 1, 1, 1, 1
        Button:
            text: "Load Selected Campaign"
            on_press: root.load_campaign()
            background_color: 0.2, 0.7, 0.7, 1
            color: 1, 1, 1, 1

    # Delay
    BoxLayout:
        size_hint_y: None
        height: 40
        spacing: 10
        Label:
            text: "Delay (sec):"
            size_hint_x: None
            width: 100
            color: 0.2, 0.2, 0.2, 1
        TextInput:
            id: delay_input
            text: str(root.delay)
            input_filter: 'float'
            multiline: False
            disabled: root.running
            on_text: root.validate_delay(self.text)
            size_hint_x: 1
            background_color: 1, 1, 1, 1
            foreground_color: 0, 0, 0, 1

    # Start index & max send
    BoxLayout:
        size_hint_y: None
        height: 40
        spacing: 10
        Label:
            text: "Start from (#):"
            size_hint_x: None
            width: 100
            color: 0.2, 0.2, 0.2, 1
        TextInput:
            id: start_index_input
            text: str(root.start_index)
            input_filter: 'int'
            multiline: False
            disabled: root.running
            on_text: root.set_start_index(self.text)
            size_hint_x: 0.5
            background_color: 1, 1, 1, 1
            foreground_color: 0, 0, 0, 1
        Label:
            text: "Max send (0=all):"
            size_hint_x: None
            width: 120
            color: 0.2, 0.2, 0.2, 1
        TextInput:
            id: max_send_input
            text: str(root.max_send)
            input_filter: 'int'
            multiline: False
            disabled: root.running
            on_text: root.set_max_send(self.text)
            size_hint_x: 0.5
            background_color: 1, 1, 1, 1
            foreground_color: 0, 0, 0, 1

    # Control buttons
    BoxLayout:
        size_hint_y: None
        height: 50
        spacing: 10
        Button:
            text: "Start Sending"
            background_color: 0.1, 0.6, 0.1, 1
            color: 1, 1, 1, 1
            font_size: 18
            disabled: root.running or root.total_recipients == 0 or root.current_template_index < 0
            on_press: root.confirm_start()
        Button:
            id: stop_resume_btn
            text: "Stop"
            background_color: 0.9, 0.2, 0.2, 1
            color: 1, 1, 1, 1
            font_size: 18
            disabled: True
            on_press: root.toggle_pause_resume()
        Button:
            text: "Test Send"
            background_color: 0.4, 0.4, 0.8, 1
            color: 1, 1, 1, 1
            font_size: 18
            disabled: root.running or root.total_recipients == 0 or root.current_template_index < 0
            on_press: root.test_send()
        Button:
            text: "Clear All"
            background_color: 0.5, 0.5, 0.5, 1
            color: 1, 1, 1, 1
            font_size: 18
            on_press: root.reset()

    # Progress
    Label:
        id: status_label
        text: f"Ready: {root.total_recipients} recipients"
        size_hint_y: None
        height: 25
        color: 0.1, 0.1, 0.1, 1
    Label:
        id: sent_label
        text: f"Sent: {root.sent}"
        size_hint_y: None
        height: 25
        color: 0.1, 0.1, 0.1, 1
    ProgressBar:
        max: root.total_recipients
        value: root.sent
        size_hint_y: None
        height: 20
'''

class WhatsAppSender(BoxLayout):
    delay = NumericProperty(7)
    sent = NumericProperty(0)
    total_recipients = NumericProperty(0)
    running = BooleanProperty(False)
    current_template_index = NumericProperty(-1)
    template_options = ListProperty([])
    rotate_templates = BooleanProperty(False)
    campaign_list = ListProperty([])
    start_index = NumericProperty(0)
    max_send = NumericProperty(0)
    current_campaign_name = StringProperty('')
    has_pending = BooleanProperty(False)   # NEW: to show Resume button

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.recipients = []
        self.templates = []
        self._event = None
        self._rotate_index = 0
        self._send_queue = []
        self._session_start_index = 0
        self.storage_path = os.path.join(App.get_running_app().user_data_dir, 'templates.json')
        self.campaigns_path = os.path.join(App.get_running_app().user_data_dir, 'campaigns.json')
        self.report_path = os.path.join(App.get_running_app().user_data_dir, 'sending_report.txt')
        self.load_templates()
        self.load_campaign_list()

    # ------------------- Data Processing -------------------
    def on_data_change(self, *args):
        numbers_text = self.ids.numbers_input.text
        names_text = self.ids.names_input.text
        addresses_text = self.ids.addresses_input.text

        raw_numbers = [line.strip() for line in numbers_text.split('\n') if line.strip()]
        names = [line.strip() for line in names_text.split('\n') if line.strip()]
        addresses = [line.strip() for line in addresses_text.split('\n') if line.strip()]

        self.recipients = []
        max_len = max(len(raw_numbers), len(names), len(addresses))
        for i in range(max_len):
            phone_raw = raw_numbers[i] if i < len(raw_numbers) else ''
            name = names[i] if i < len(names) else ''
            address = addresses[i] if i < len(addresses) else ''

            phone_clean = re.sub(r'[^\d+]', '', phone_raw)
            if not phone_clean:
                continue
            if not phone_clean.startswith('+'):
                phone_clean = '+' + phone_clean
            if re.match(r'^\+\d+$', phone_clean):
                self.recipients.append((phone_clean, name, address))
            else:
                Logger.warning(f"Skipping invalid phone: {phone_raw}")

        self.total_recipients = len(self.recipients)
        self.ids.status_label.text = f"Ready: {self.total_recipients} recipients"

        # Clear any pending queue when data changes
        self._send_queue = []
        self.has_pending = False
        self._update_stop_resume_button()

    # ------------------- Templates -------------------
    def load_templates(self):
        try:
            if os.path.exists(self.storage_path):
                with open(self.storage_path, 'r', encoding='utf-8') as f:
                    self.templates = json.load(f)
            else:
                self.templates = []
        except Exception as e:
            Logger.error(f"Failed to load templates: {e}")
            self.templates = []
        self.refresh_spinner()
        if self.templates:
            self.ids.template_spinner.text = self.template_options[0]
            self.on_template_select(self.template_options[0])
        else:
            self.current_template_index = -1
            self.ids.template_edit.text = ""

    def save_templates_to_file(self):
        try:
            with open(self.storage_path, 'w', encoding='utf-8') as f:
                json.dump(self.templates, f, ensure_ascii=False, indent=2)
        except Exception as e:
            Logger.error(f"Failed to save templates: {e}")

    def refresh_spinner(self):
        self.template_options = [f"Template {i+1}" for i in range(len(self.templates))]
        if self.current_template_index >= len(self.templates):
            self.current_template_index = -1

    def on_template_select(self, spinner_text):
        idx = self.template_options.index(spinner_text) if spinner_text in self.template_options else -1
        if idx >= 0:
            self.current_template_index = idx
            self.ids.template_edit.text = self.templates[idx]
        else:
            self.current_template_index = -1
            self.ids.template_edit.text = ""

    def save_current_template(self):
        idx = self.current_template_index
        if idx < 0 or idx >= len(self.templates):
            return
        new_text = self.ids.template_edit.text
        self.templates[idx] = new_text
        self.save_templates_to_file()
        Logger.info(f"Template {idx+1} updated.")

    def new_template(self):
        self.templates.append("Hello {name}, your address is {address}.")
        self.save_templates_to_file()
        self.refresh_spinner()
        self.current_template_index = len(self.templates) - 1
        self.ids.template_spinner.text = self.template_options[self.current_template_index]
        self.ids.template_edit.text = self.templates[self.current_template_index]

    def delete_template(self):
        idx = self.current_template_index
        if idx < 0:
            return
        del self.templates[idx]
        self.save_templates_to_file()
        self.refresh_spinner()
        if self.templates:
            self.current_template_index = 0
            self.ids.template_spinner.text = self.template_options[0]
            self.ids.template_edit.text = self.templates[0]
        else:
            self.current_template_index = -1
            self.ids.template_spinner.text = "Select Template"
            self.ids.template_edit.text = ""

    # ------------------- Campaigns -------------------
    def load_campaign_list(self):
        campaigns = self._load_all_campaigns()
        self.campaign_list = sorted(campaigns.keys())
        if hasattr(self.ids, 'campaign_spinner'):
            self.ids.campaign_spinner.values = self.campaign_list if self.campaign_list else ["No campaigns saved"]
            self.ids.campaign_spinner.text = "Load Campaign"

    def _load_all_campaigns(self):
        if not os.path.exists(self.campaigns_path):
            return {}
        try:
            with open(self.campaigns_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except:
            return {}

    def _save_all_campaigns(self, campaigns):
        try:
            with open(self.campaigns_path, 'w', encoding='utf-8') as f:
                json.dump(campaigns, f, ensure_ascii=False, indent=2)
        except Exception as e:
            Logger.error(f"Failed to save campaigns: {e}")

    def save_campaign(self):
        name = self.ids.campaign_name_input.text.strip()
        if not name:
            self.show_popup("Error", "Please enter a campaign name.")
            return
        campaigns = self._load_all_campaigns()
        old_sent = 0
        if name in campaigns:
            old_sent = campaigns[name].get('sent_count', 0)
        campaign_data = {
            "numbers": self.ids.numbers_input.text,
            "names": self.ids.names_input.text,
            "addresses": self.ids.addresses_input.text,
            "templates": self.templates,
            "current_template_index": self.current_template_index,
            "delay": self.delay,
            "rotate": self.rotate_templates,
            "sent_count": old_sent
        }
        campaigns[name] = campaign_data
        self._save_all_campaigns(campaigns)
        self.load_campaign_list()
        Logger.info(f"Campaign '{name}' saved successfully.")
        self.show_popup("Success", f"Campaign '{name}' saved.")
        self.ids.campaign_name_input.text = ""
        self.current_campaign_name = name

    def load_campaign(self):
        selected = self.ids.campaign_spinner.text
        if selected == "Load Campaign" or selected == "No campaigns saved":
            self.show_popup("Error", "No campaign selected.")
            return
        campaigns = self._load_all_campaigns()
        if selected not in campaigns:
            self.show_popup("Error", f"Campaign '{selected}' not found.")
            return
        campaign = campaigns[selected]
        self.ids.numbers_input.text = campaign.get("numbers", "")
        self.ids.names_input.text = campaign.get("names", "")
        self.ids.addresses_input.text = campaign.get("addresses", "")
        self.templates = campaign.get("templates", [])
        self.save_templates_to_file()
        self.refresh_spinner()
        idx = campaign.get("current_template_index", -1)
        if 0 <= idx < len(self.templates):
            self.current_template_index = idx
            self.ids.template_spinner.text = self.template_options[idx]
            self.ids.template_edit.text = self.templates[idx]
        else:
            self.current_template_index = -1
            self.ids.template_spinner.text = "Select Template"
            self.ids.template_edit.text = ""
        self.delay = campaign.get("delay", 7)
        self.ids.delay_input.text = str(self.delay)
        self.rotate_templates = campaign.get("rotate", False)
        self.ids.rotate_checkbox.active = self.rotate_templates

        sent_count = campaign.get("sent_count", 0)
        self.start_index = sent_count
        self.ids.start_index_input.text = str(sent_count)
        self.max_send = 0
        self.ids.max_send_input.text = "0"

        self.current_campaign_name = selected
        self._send_queue = []   # reset pending queue on new campaign load
        self.has_pending = False
        self._update_stop_resume_button()
        self.on_data_change()
        self.show_popup("Success", f"Campaign '{selected}' loaded.\nAlready sent: {sent_count}")

    def delete_campaign(self):
        selected = self.ids.campaign_spinner.text
        if selected == "Load Campaign" or selected == "No campaigns saved":
            return
        campaigns = self._load_all_campaigns()
        if selected in campaigns:
            del campaigns[selected]
            self._save_all_campaigns(campaigns)
            self.load_campaign_list()
            if self.current_campaign_name == selected:
                self.current_campaign_name = ''
            Logger.info(f"Campaign '{selected}' deleted.")
            self.show_popup("Success", f"Campaign '{selected}' deleted.")

    def update_campaign_progress(self, new_total_sent):
        if not self.current_campaign_name:
            return
        campaigns = self._load_all_campaigns()
        if self.current_campaign_name in campaigns:
            campaigns[self.current_campaign_name]['sent_count'] = new_total_sent
            self._save_all_campaigns(campaigns)
            Logger.info(f"Campaign '{self.current_campaign_name}' progress updated to {new_total_sent}")

    # ------------------- Start/Max send setters -------------------
    def set_start_index(self, text):
        try:
            val = int(text)
            if val < 0:
                val = 0
            self.start_index = val
            self.ids.start_index_input.text = str(val)
        except:
            pass

    def set_max_send(self, text):
        try:
            val = int(text)
            if val < 0:
                val = 0
            self.max_send = val
            self.ids.max_send_input.text = str(val)
        except:
            pass

    # ------------------- Delay -------------------
    def validate_delay(self, value):
        try:
            d = float(value)
            if d < 3:
                d = 3.0
            self.delay = d
            self.ids.delay_input.text = str(d)
        except:
            pass

    # ------------------- Popup Helper -------------------
    def show_popup(self, title, message):
        content = GridLayout(cols=1, padding=10, spacing=10)
        content.add_widget(Label(text=message, halign='center', valign='middle'))
        btn = Button(text="OK", size_hint_y=None, height=40)
        content.add_widget(btn)
        popup = Popup(title=title, content=content, size_hint=(0.6, 0.4), auto_dismiss=False)
        btn.bind(on_press=popup.dismiss)
        popup.open()

    # ------------------- Confirmation Dialog -------------------
    def confirm_start(self):
        if self.running:
            return
        self.on_data_change()
        if not self.recipients:
            self.show_popup("Error", "No valid recipients.")
            return
        if self.current_template_index < 0 or not self.templates:
            self.show_popup("Error", "No template selected.")
            return

        queue = self.recipients[self.start_index:]
        max_send = self.max_send
        total_to_send = len(queue) if max_send == 0 else min(len(queue), max_send)
        content = GridLayout(cols=1, padding=10, spacing=10)
        content.add_widget(Label(
            text=f"Send to {total_to_send} recipients?\nStart from #{self.start_index}\nDelay: {self.delay} sec\nTemplate: {self.ids.template_spinner.text}",
            halign='center', valign='middle'
        ))
        btn_box = BoxLayout(size_hint_y=None, height=40, spacing=10)
        btn_yes = Button(text="Yes", background_color=(0.2, 0.7, 0.2, 1))
        btn_no = Button(text="No", background_color=(0.7, 0.2, 0.2, 1))
        btn_box.add_widget(btn_yes)
        btn_box.add_widget(btn_no)
        content.add_widget(btn_box)

        popup = Popup(title="Confirm Send", content=content, size_hint=(0.7, 0.5), auto_dismiss=False)
        def on_yes(instance):
            popup.dismiss()
            Clock.schedule_once(lambda dt: self.start_sending(), 0.1)
        def on_no(instance):
            popup.dismiss()
        btn_yes.bind(on_press=on_yes)
        btn_no.bind(on_press=on_no)
        popup.open()

    # ------------------- Sending -------------------
    def start_sending(self):
        if self.running:
            return
        # If we already have a pending queue, we are resuming
        if not self._send_queue:
            # New session
            self.sent = 0
            self._rotate_index = self.current_template_index
            queue = self.recipients[self.start_index:]
            if self.max_send > 0:
                queue = queue[:self.max_send]
            self._send_queue = queue
            self._session_start_index = self.start_index
        else:
            # Resuming – sent already reflects previous progress
            # Keep current sent and queue as is
            pass

        self.running = True
        self._start_report()
        Logger.info(f"Starting/resuming send from index {self._session_start_index}, queue size: {len(self._send_queue)}")
        self._update_stop_resume_button()
        self._event = Clock.schedule_once(self.send_next, 0)

    def stop_sending(self):
        if self._event:
            self._event.cancel()
        self.running = False
        total_sent = self._session_start_index + self.sent
        self._write_report("Sending paused by user.")
        Logger.info(f"Sending paused after {self.sent} messages (total: {total_sent})")
        self.update_campaign_progress(total_sent)
        # Update start_index so next "Start" would skip already sent ones
        self.start_index = total_sent
        self.ids.start_index_input.text = str(total_sent)
        self._update_stop_resume_button()

    def toggle_pause_resume(self):
        if self.running:
            self.stop_sending()
        else:
            # Resume if there is pending queue
            if self._send_queue:
                self.start_sending()

    def _update_stop_resume_button(self):
        btn = self.ids.stop_resume_btn
        if self.running:
            btn.text = "Stop"
            btn.background_color = (0.9, 0.2, 0.2, 1)
            btn.disabled = False
        else:
            if self._send_queue:
                btn.text = "Resume"
                btn.background_color = (0.2, 0.6, 0.8, 1)  # blue-ish
                btn.disabled = False
                self.has_pending = True
            else:
                btn.text = "Stop"
                btn.background_color = (0.9, 0.2, 0.2, 1)
                btn.disabled = True
                self.has_pending = False

    def send_next(self, dt):
        if not self.running or not self._send_queue:
            if not self._send_queue:
                self.running = False
                total_sent = self._session_start_index + self.sent
                self._write_report("All messages processed.")
                Logger.info(f"All {self.sent} messages processed (total: {total_sent})")
                self.show_popup("Completed", f"All {self.sent} messages processed.")
                self.update_campaign_progress(total_sent)
                self.start_index = total_sent
                self.ids.start_index_input.text = str(total_sent)
                self._send_queue = []
                self._update_stop_resume_button()
            return

        phone, name, address = self._send_queue.pop(0)

        if self.rotate_templates and self.templates:
            template = self.templates[self._rotate_index % len(self.templates)]
            self._rotate_index += 1
        else:
            template = self.templates[self.current_template_index]

        message = template.replace('{name}', name).replace('{address}', address)

        try:
            encoded = quote(message, safe='')
            url = f"https://wa.me/{phone}?text={encoded}"
            Logger.info(f"Opening WhatsApp for {phone} ({name}, {address})")
            webbrowser.open(url)
            self.sent += 1
            self.ids.sent_label.text = f"Sent: {self.sent}"
            self._log_send(phone, name, address, message)
        except Exception as e:
            Logger.error(f"Failed to open for {phone}: {e}")
            self._log_error(phone, name, address, str(e))

        if not self._send_queue:
            self.running = False
            total_sent = self._session_start_index + self.sent
            self._write_report("All messages processed.")
            Logger.info(f"All {self.sent} messages processed (total: {total_sent})")
            self.show_popup("Completed", f"All {self.sent} messages processed.")
            self.update_campaign_progress(total_sent)
            self.start_index = total_sent
            self.ids.start_index_input.text = str(total_sent)
            self._send_queue = []
            self._update_stop_resume_button()
        elif self.running:
            self._event = Clock.schedule_once(self.send_next, self.delay)

    # ------------------- Test Send -------------------
    def test_send(self):
        self.on_data_change()
        if not self.recipients:
            self.show_popup("Error", "No valid recipients.")
            return
        if self.current_template_index < 0 or not self.templates:
            self.show_popup("Error", "No template selected.")
            return
        phone, name, address = self.recipients[0]
        template = self.templates[self.current_template_index]
        message = template.replace('{name}', name).replace('{address}', address)
        encoded = quote(message, safe='')
        url = f"https://wa.me/{phone}?text={encoded}"
        webbrowser.open(url)
        self.show_popup("Test", f"Opened WhatsApp for {phone} (first recipient).")

    # ------------------- Report -------------------
    def _start_report(self):
        with open(self.report_path, 'a', encoding='utf-8') as f:
            f.write(f"\n\n========== New Session: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} ==========\n")

    def _log_send(self, phone, name, address, message):
        with open(self.report_path, 'a', encoding='utf-8') as f:
            f.write(f"[OK] {datetime.now().strftime('%H:%M:%S')} - {phone} ({name}, {address}) - Message: {message[:50]}...\n")

    def _log_error(self, phone, name, address, error):
        with open(self.report_path, 'a', encoding='utf-8') as f:
            f.write(f"[ERROR] {datetime.now().strftime('%H:%M:%S')} - {phone} ({name}, {address}) - {error}\n")

    def _write_report(self, summary):
        with open(self.report_path, 'a', encoding='utf-8') as f:
            f.write(f"Summary: {summary} - Total sent: {self.sent}\n")

    # ------------------- Reset -------------------
    def reset(self):
        self.stop_sending()
        self.ids.numbers_input.text = ""
        self.ids.names_input.text = ""
        self.ids.addresses_input.text = ""
        self.recipients = []
        self.sent = 0
        self.total_recipients = 0
        self.start_index = 0
        self.max_send = 0
        self.ids.start_index_input.text = "0"
        self.ids.max_send_input.text = "0"
        self.ids.status_label.text = "Ready: 0 recipients"
        self.ids.sent_label.text = "Sent: 0"
        self._send_queue = []
        self.has_pending = False
        self.current_campaign_name = ''
        self._update_stop_resume_button()
        Logger.info("Reset completed.")
        self.show_popup("Reset", "All data cleared.")

class WhatsAppSenderApp(App):
    def build(self):
        self.title = "WhatsApp Bulk Sender"
        Window.maximize()
        Builder.load_string(KV)
        return WhatsAppSender()

if __name__ == '__main__':
    WhatsAppSenderApp().run()