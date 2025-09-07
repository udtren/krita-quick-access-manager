from PyQt5.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QSlider, QGridLayout
from PyQt5.QtCore import Qt, QTimer
from krita import Krita
from .preprocess import check_common_config

COMMON_CONFIG = check_common_config()

def get_brush_adjustment_style():
    color = COMMON_CONFIG["color"]["docker_button_background_color"]
    font_color = COMMON_CONFIG["color"]["docker_button_font_color"]
    font_size = COMMON_CONFIG["font"]["docker_button_font_size"]
    return f"color: {font_color}; font-size: {font_size};"

class BrushAdjustmentWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent_docker = parent
        self.current_brush_name = None
        self.current_brush_size = None
        self.current_brush_opacity = None  # Add opacity tracking
        self.current_brush_rotation = None
        self.updating_from_brush = False  # Flag to prevent recursive updates
        self.init_ui()
        
        # Timer to periodically check for brush changes
        self.brush_check_timer = QTimer()
        self.brush_check_timer.timeout.connect(self.check_brush_change)
        self.brush_check_timer.start(200)  # Check every 200ms for more responsiveness
        
    def init_ui(self):
        layout = QVBoxLayout()
        layout.setContentsMargins(5, 5, 5, 5)
        layout.setSpacing(8)
        
        # Create horizontal layout for single row
        main_layout = QHBoxLayout()
        main_layout.setSpacing(8)
        
        # Size slider with value
        size_layout = QHBoxLayout()
        size_layout.setSpacing(4)
        
        self.size_slider = QSlider(Qt.Horizontal)
        self.size_slider.setMinimum(1)
        self.size_slider.setMaximum(1000)
        self.size_slider.setValue(10)
        self.size_slider.valueChanged.connect(self.on_size_changed)
        
        self.size_value_label = QLabel("10")
        self.size_value_label.setStyleSheet(get_brush_adjustment_style())
        self.size_value_label.setAlignment(Qt.AlignCenter)
        self.size_value_label.setFixedWidth(30)
        
        size_layout.addWidget(self.size_slider, 1)
        size_layout.addWidget(self.size_value_label)
        
        # Opacity slider with value
        opacity_layout = QHBoxLayout()
        opacity_layout.setSpacing(4)
        
        self.opacity_slider = QSlider(Qt.Horizontal)
        self.opacity_slider.setMinimum(0)
        self.opacity_slider.setMaximum(100)
        self.opacity_slider.setValue(100)
        self.opacity_slider.valueChanged.connect(self.on_opacity_changed)
        
        self.opacity_value_label = QLabel("100%")
        self.opacity_value_label.setStyleSheet(get_brush_adjustment_style())
        self.opacity_value_label.setAlignment(Qt.AlignCenter)
        self.opacity_value_label.setFixedWidth(35)
        
        opacity_layout.addWidget(self.opacity_slider, 1)
        opacity_layout.addWidget(self.opacity_value_label)
        
        # Rotation slider with value
        rotation_layout = QHBoxLayout()
        rotation_layout.setSpacing(4)
        
        self.rotation_slider = QSlider(Qt.Horizontal)
        self.rotation_slider.setMinimum(0)
        self.rotation_slider.setMaximum(360)
        self.rotation_slider.setValue(0)
        self.rotation_slider.valueChanged.connect(self.on_rotation_changed)
        
        self.rotation_value_label = QLabel("0°")
        self.rotation_value_label.setStyleSheet(get_brush_adjustment_style())
        self.rotation_value_label.setAlignment(Qt.AlignCenter)
        self.rotation_value_label.setFixedWidth(30)
        
        rotation_layout.addWidget(self.rotation_slider, 1)
        rotation_layout.addWidget(self.rotation_value_label)
        
        # Add all slider groups to main layout
        main_layout.addLayout(size_layout, 1)
        main_layout.addLayout(opacity_layout, 1)
        main_layout.addLayout(rotation_layout, 1)
        
        layout.addLayout(main_layout)
        self.setLayout(layout)
        
        # Load current brush settings
        self.update_from_current_brush()

    def check_brush_change(self):
        """Check if the current brush has changed and update sliders if needed"""
        app = Krita.instance()
        if app.activeWindow() and app.activeWindow().activeView():
            view = app.activeWindow().activeView()
            try:
                current_preset = view.currentBrushPreset()
                if current_preset:
                    brush_name = current_preset.name()
                    
                    # Get current brush properties
                    current_size = None
                    current_opacity = None
                    current_rotation = None
                    
                    try:
                        current_size = view.brushSize()
                    except:
                        pass
                    
                    try:
                        current_opacity = view.paintingOpacity()
                    except:
                        pass
                    
                    try:
                        current_rotation = view.brushRotation()
                    except:
                        pass
                    
                    # Check if brush name changed OR if properties changed (for reload preset action)
                    brush_changed = brush_name != self.current_brush_name
                    size_changed = current_size != self.current_brush_size
                    opacity_changed = current_opacity != self.current_brush_opacity
                    rotation_changed = current_rotation != self.current_brush_rotation
                    
                    if brush_changed or size_changed or opacity_changed or rotation_changed:
                        self.current_brush_name = brush_name
                        self.current_brush_size = current_size
                        self.current_brush_opacity = current_opacity
                        self.current_brush_rotation = current_rotation
                        self.update_from_current_brush()
            except:
                pass
        
    def update_from_current_brush(self):
        """Update sliders to match current brush settings"""
        if self.updating_from_brush:
            return
            
        self.updating_from_brush = True
        
        app = Krita.instance()
        if app.activeWindow() and app.activeWindow().activeView():
            view = app.activeWindow().activeView()
            
            # Get current brush size directly from the view
            try:
                size = view.brushSize()
                self.size_slider.setValue(int(size))
                self.size_value_label.setText(str(int(size)))
                self.current_brush_size = size
            except:
                # Fallback to default if brushSize() doesn't work
                self.size_slider.setValue(10)
                self.size_value_label.setText("10")
                self.current_brush_size = 10
            
            # Get current opacity
            try:
                opacity = view.paintingOpacity()
                opacity_percent = int(opacity * 100)  # Convert from 0-1 to 0-100
                self.opacity_slider.setValue(opacity_percent)
                self.opacity_value_label.setText(f"{opacity_percent}%")
                self.current_brush_opacity = opacity
            except:
                # Fallback if opacity method doesn't work
                self.opacity_slider.setValue(100)
                self.opacity_value_label.setText("100%")
                self.current_brush_opacity = 1.0
            
            # Get brush rotation - this might need different approach
            try:
                rotation = view.brushRotation()
                self.rotation_slider.setValue(int(rotation))
                self.rotation_value_label.setText(f"{int(rotation)}°")
                self.current_brush_rotation = rotation
            except:
                # Fallback if rotation method doesn't exist
                self.rotation_slider.setValue(0)
                self.rotation_value_label.setText("0°")
                self.current_brush_rotation = 0
        
        self.updating_from_brush = False

    def on_size_changed(self, value):
        """Handle brush size change"""
        if self.updating_from_brush:
            return
            
        self.size_value_label.setText(str(value))
        self.current_brush_size = value  # Update tracked value
        
        app = Krita.instance()
        if app.activeWindow() and app.activeWindow().activeView():
            view = app.activeWindow().activeView()
            try:
                # Set brush size directly on the view
                view.setBrushSize(float(value))
            except Exception as e:
                print(f"Error setting brush size: {e}")

    def on_opacity_changed(self, value):
        """Handle brush opacity change"""
        if self.updating_from_brush:
            return
            
        self.opacity_value_label.setText(f"{value}%")
        opacity_float = value / 100.0  # Convert from 0-100 to 0-1
        self.current_brush_opacity = opacity_float  # Update tracked value
        
        app = Krita.instance()
        if app.activeWindow() and app.activeWindow().activeView():
            view = app.activeWindow().activeView()
            try:
                # Set opacity directly on the view
                view.setPaintingOpacity(opacity_float)
            except Exception as e:
                print(f"Error setting brush opacity: {e}")

    def on_rotation_changed(self, value):
        """Handle brush rotation change"""
        if self.updating_from_brush:
            return
            
        self.rotation_value_label.setText(f"{value}°")
        self.current_brush_rotation = value  # Update tracked value
        
        app = Krita.instance()
        if app.activeWindow() and app.activeWindow().activeView():
            view = app.activeWindow().activeView()
            try:
                # Set brush rotation directly on the view
                view.setBrushRotation(float(value))
            except Exception as e:
                print(f"Error setting brush rotation: {e}")
    
    def force_update(self):
        """Force update from current brush - can be called externally"""
        self.current_brush_name = None
        self.current_brush_size = None
        self.current_brush_opacity = None
        self.current_brush_rotation = None
        self.update_from_current_brush()
    
    def refresh_styles(self):
        """Refresh styles when settings change"""
        style = get_brush_adjustment_style()
        for label in self.findChildren(QLabel):
            if label.text() not in ["Brush Adjustments"]:  # Skip title
                label.setStyleSheet(style)

    def closeEvent(self, event):
        """Clean up timer when widget is closed"""
        if hasattr(self, 'brush_check_timer'):
            self.brush_check_timer.stop()
        super().closeEvent(event)