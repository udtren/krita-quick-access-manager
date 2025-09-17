from PyQt5.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QSlider, QGridLayout, QPushButton
from PyQt5.QtCore import Qt, QTimer, pyqtSignal
from PyQt5.QtGui import QPainter, QPen, QBrush, QColor, QPolygon
from krita import Krita
import math

# Font size for brush adjustment labels (easily adjustable)
BRUSH_ADJUSTMENT_FONT_SIZE = "12px"
BRUSH_ADJUSTMENT_NUMBER_SIZE = "16px"
COLOR_HISTORY_NUMBER = 20

class ColorHistoryWidget(QWidget):
    """Widget to display color history in a grid"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.color_history = []
        self.color_buttons = []
        self.init_ui()
        
        # Timer to periodically check for color changes
        self.color_check_timer = QTimer()
        self.color_check_timer.timeout.connect(self.check_color_change)
        self.color_check_timer.start(200)  # Check every 200ms for better responsiveness
        
    def init_ui(self):
        layout = QVBoxLayout()
        layout.setContentsMargins(2, 2, 2, 2)
        layout.setSpacing(2)
        
        # Create 2 rows for color history
        colors_per_row = COLOR_HISTORY_NUMBER // 2
        button_size = 20
        
        # First row
        row1_layout = QHBoxLayout()
        row1_layout.setSpacing(1)
        row1_layout.setContentsMargins(0, 0, 0, 0)
        
        # Second row
        row2_layout = QHBoxLayout()
        row2_layout.setSpacing(1)
        row2_layout.setContentsMargins(0, 0, 0, 0)
        
        # Create color buttons
        for i in range(COLOR_HISTORY_NUMBER):
            color_btn = QPushButton()
            color_btn.setFixedSize(button_size, button_size)
            color_btn.setStyleSheet("border: 1px solid #888; background-color: #f0f0f0;")
            color_btn.clicked.connect(lambda checked, idx=i: self.on_color_clicked(idx))
            self.color_buttons.append(color_btn)
            
            # Add to appropriate row
            if i < colors_per_row:
                row1_layout.addWidget(color_btn)
            else:
                row2_layout.addWidget(color_btn)
        
        layout.addLayout(row1_layout)
        layout.addLayout(row2_layout)
        self.setLayout(layout)
        
    def check_color_change(self):
        """Check if the current foreground color has changed"""
        app = Krita.instance()
        if app.activeWindow() and app.activeWindow().activeView():
            view = app.activeWindow().activeView()
            try:
                # Get current foreground color
                fg_color = view.foregroundColor()
                if fg_color:
                    # Get color components and convert to 0-255 range
                    components = fg_color.components()
                    if len(components) >= 3:
                        color_rgb = (
                            int(components[0] * 255),
                            int(components[1] * 255), 
                            int(components[2] * 255)
                        )
                        
                        # Add to history if it's different from the last color
                        if not self.color_history or self.color_history[0] != color_rgb:
                            self.add_color_to_history(color_rgb)
            except Exception as e:
                # Try alternative method
                try:
                    fg_color = view.foregroundColor()
                    if fg_color:
                        # Try using colorProfile and colorSpace
                        color_rgb = (
                            int(fg_color.red() * 255),
                            int(fg_color.green() * 255),
                            int(fg_color.blue() * 255)
                        )
                        
                        # Add to history if it's different from the last color
                        if not self.color_history or self.color_history[0] != color_rgb:
                            self.add_color_to_history(color_rgb)
                except Exception as e2:
                    print(f"Error getting foreground color: {e2}")
                    pass
    
    def add_color_to_history(self, color_rgb):
        """Add a color to the history and update display"""
        print(f"Adding color to history: RGB{color_rgb}")  # Debug output
        
        # Remove color if it already exists in history
        if color_rgb in self.color_history:
            self.color_history.remove(color_rgb)
        
        # Add to front of history
        self.color_history.insert(0, color_rgb)
        
        # Limit history size
        if len(self.color_history) > COLOR_HISTORY_NUMBER:
            self.color_history = self.color_history[:COLOR_HISTORY_NUMBER]
        
        # Update button colors
        self.update_color_buttons()
        print(f"Color history now has {len(self.color_history)} colors")  # Debug output
    
    def update_color_buttons(self):
        """Update the color buttons to show current history"""
        for i, btn in enumerate(self.color_buttons):
            if i < len(self.color_history):
                r, g, b = self.color_history[i]
                btn.setStyleSheet(f"border: 1px solid #888; background-color: rgb({r}, {g}, {b});")
                btn.setToolTip(f"RGB({r}, {g}, {b})")
            else:
                btn.setStyleSheet("border: 1px solid #888; background-color: #f0f0f0;")
                btn.setToolTip("")
    
    def on_color_clicked(self, index):
        """Handle color button click to set foreground color"""
        if index < len(self.color_history):
            r, g, b = self.color_history[index]
            print(f"Clicking color: RGB({r}, {g}, {b})")  # Debug output
            
            app = Krita.instance()
            if app.activeWindow() and app.activeWindow().activeView():
                view = app.activeWindow().activeView()
                
                success = False
                
                # Method 1: Try using ManagedColor with proper color space
                try:
                    from krita import ManagedColor
                    color = ManagedColor("RGBA", "U8", "")
                    
                    # Try to get the document's color profile
                    if view.document() and view.document().colorProfile():
                        color.setColorProfile(view.document().colorProfile())
                    elif view.canvas() and view.canvas().colorProfile():
                        color.setColorProfile(view.canvas().colorProfile())
                    
                    # Set the color components directly
                    color.setComponents([r/255.0, g/255.0, b/255.0, 1.0])
                    view.setForeGroundColor(color)
                    success = True
                    print(f"Successfully set color using ManagedColor")
                except Exception as e:
                    print(f"Method 1 failed: {e}")
                
                # Method 2: Try using QColor conversion if Method 1 failed
                if not success:
                    try:
                        from krita import ManagedColor
                        color = ManagedColor("RGBA", "U8", "")
                        color.fromQColor(QColor(r, g, b))
                        view.setForeGroundColor(color)
                        success = True
                        print(f"Successfully set color using QColor conversion")
                    except Exception as e:
                        print(f"Method 2 failed: {e}")
                
                # Method 3: Try modifying existing foreground color if previous methods failed
                if not success:
                    try:
                        current_color = view.foregroundColor()
                        if current_color:
                            current_color.setComponents([r/255.0, g/255.0, b/255.0, 1.0])
                            view.setForeGroundColor(current_color)
                            success = True
                            print(f"Successfully set color by modifying existing color")
                    except Exception as e:
                        print(f"Method 3 failed: {e}")
                
                if success:
                    # Move this color to front of history since it was used
                    self.add_color_to_history((r, g, b))
                    print(f"Color set successfully and moved to front of history")
                else:
                    print(f"All methods failed to set foreground color to RGB({r}, {g}, {b})")
    
    def force_color_update(self):
        """Force an immediate color history update"""
        self.check_color_change()
    
    def add_test_color(self):
        """Add a test color to verify the widget is working"""
        import random
        test_color = (random.randint(0, 255), random.randint(0, 255), random.randint(0, 255))
        self.add_color_to_history(test_color)
        print(f"Added test color: RGB{test_color}")
    
    def closeEvent(self, event):
        """Clean up timer when widget is closed"""
        if hasattr(self, 'color_check_timer'):
            self.color_check_timer.stop()
        super().closeEvent(event)

class CircularRotationWidget(QWidget):
    """Custom circular rotation control widget"""
    valueChanged = pyqtSignal(int)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedSize(60, 60)  # Fixed square size
        self.value = 0  # 0-360 degrees
        self.dragging = False
        self.setMouseTracking(True)
        
    def setValue(self, value):
        """Set the rotation value (0-360)"""
        self.value = max(0, min(360, value))
        self.update()
        
    def getValue(self):
        """Get the current rotation value"""
        return self.value
    
    def paintEvent(self, event):
        """Custom paint event to draw the circular control"""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        # Get widget center and radius
        center_x = self.width() // 2
        center_y = self.height() // 2
        radius = min(center_x, center_y) - 5
        
        # Draw outer circle (track)
        painter.setPen(QPen(QColor(128, 128, 128), 2))
        painter.setBrush(QBrush(QColor(240, 240, 240)))
        painter.drawEllipse(center_x - radius, center_y - radius, radius * 2, radius * 2)
        
        # Draw rotation indicator line
        angle_rad = math.radians(self.value - 90)  # -90 to start from top
        end_x = center_x + (radius - 10) * math.cos(angle_rad)
        end_y = center_y + (radius - 10) * math.sin(angle_rad)
        
        painter.setPen(QPen(QColor(50, 150, 250), 3))
        painter.drawLine(center_x, center_y, int(end_x), int(end_y))
        
        # Draw center dot
        painter.setBrush(QBrush(QColor(50, 150, 250)))
        painter.setPen(QPen(QColor(50, 150, 250)))
        painter.drawEllipse(center_x - 3, center_y - 3, 6, 6)
        
    def mousePressEvent(self, event):
        """Handle mouse press for dragging"""
        if event.button() == Qt.LeftButton:
            self.dragging = True
            self.updateValueFromMouse(event.pos())
            
    def mouseMoveEvent(self, event):
        """Handle mouse move for dragging"""
        if self.dragging:
            self.updateValueFromMouse(event.pos())
            
    def mouseReleaseEvent(self, event):
        """Handle mouse release"""
        if event.button() == Qt.LeftButton:
            self.dragging = False
            
    def updateValueFromMouse(self, pos):
        """Update rotation value based on mouse position"""
        center_x = self.width() // 2
        center_y = self.height() // 2
        
        # Calculate angle from center to mouse position
        dx = pos.x() - center_x
        dy = pos.y() - center_y
        
        angle_rad = math.atan2(dy, dx)
        angle_deg = math.degrees(angle_rad) + 90  # +90 to start from top
        
        # Normalize to 0-360
        if angle_deg < 0:
            angle_deg += 360
        elif angle_deg >= 360:
            angle_deg -= 360
            
        old_value = self.value
        self.value = int(angle_deg)
        
        if old_value != self.value:
            self.update()
            self.valueChanged.emit(self.value)

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
        layout.setSpacing(6)
        
        # Create main horizontal layout: [Size/Opacity rows] | [Rotation widget]
        main_layout = QHBoxLayout()
        main_layout.setSpacing(10)
        
        # Left side: Size and Opacity controls in vertical layout
        left_layout = QVBoxLayout()
        left_layout.setSpacing(6)
        
        # Size row: Label | Slider | Value
        size_layout = QHBoxLayout()
        size_layout.setSpacing(6)
        
        size_label = QLabel("Size:")
        size_label.setStyleSheet(f"font-size: {BRUSH_ADJUSTMENT_FONT_SIZE};")
        size_label.setFixedWidth(50)
        size_label.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        
        self.size_slider = QSlider(Qt.Horizontal)
        self.size_slider.setMinimum(0)
        self.size_slider.setMaximum(100)  # Use 0-100 range for internal scaling
        self.size_slider.setValue(self.brush_size_to_slider(10))
        self.size_slider.valueChanged.connect(self.on_size_slider_changed)
        
        self.size_value_label = QLabel("10")
        self.size_value_label.setStyleSheet(f"font-size: {BRUSH_ADJUSTMENT_NUMBER_SIZE};")
        self.size_value_label.setAlignment(Qt.AlignCenter)
        self.size_value_label.setFixedWidth(35)
        
        size_layout.addWidget(size_label)
        size_layout.addWidget(self.size_slider, 1)
        size_layout.addWidget(self.size_value_label)
        
        # Opacity row: Label | Slider | Value
        opacity_layout = QHBoxLayout()
        opacity_layout.setSpacing(6)
        
        opacity_label = QLabel("Opacity:")
        opacity_label.setStyleSheet(f"font-size: {BRUSH_ADJUSTMENT_FONT_SIZE};")
        opacity_label.setFixedWidth(50)
        opacity_label.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        
        self.opacity_slider = QSlider(Qt.Horizontal)
        self.opacity_slider.setMinimum(0)
        self.opacity_slider.setMaximum(100)
        self.opacity_slider.setValue(100)
        self.opacity_slider.valueChanged.connect(self.on_opacity_changed)
        
        self.opacity_value_label = QLabel("100%")
        self.opacity_value_label.setStyleSheet(f"font-size: {BRUSH_ADJUSTMENT_NUMBER_SIZE};")
        self.opacity_value_label.setAlignment(Qt.AlignCenter)
        self.opacity_value_label.setFixedWidth(35)
        
        opacity_layout.addWidget(opacity_label)
        opacity_layout.addWidget(self.opacity_slider, 1)
        opacity_layout.addWidget(self.opacity_value_label)
        
        # Add size and opacity to left layout
        left_layout.addLayout(size_layout)
        left_layout.addLayout(opacity_layout)
        
        # Right side: Rotation widget and value
        right_layout = QHBoxLayout()
        right_layout.setSpacing(6)
        right_layout.setAlignment(Qt.AlignCenter)
        
        self.rotation_widget = CircularRotationWidget()
        self.rotation_widget.setValue(0)
        self.rotation_widget.valueChanged.connect(self.on_rotation_changed)
        
        self.rotation_value_label = QLabel("0°")
        self.rotation_value_label.setStyleSheet(f"font-size: {BRUSH_ADJUSTMENT_NUMBER_SIZE};")
        self.rotation_value_label.setAlignment(Qt.AlignCenter | Qt.AlignVCenter)
        self.rotation_value_label.setFixedWidth(35)  # Smaller width for side placement
        
        right_layout.addWidget(self.rotation_widget)
        right_layout.addWidget(self.rotation_value_label)
        
        # Add left and right layouts to main layout
        main_layout.addLayout(left_layout, 1)  # Give left side more space
        main_layout.addLayout(right_layout)
        
        # Add main layout to the widget
        layout.addLayout(main_layout)
        
        # Add color history widget below the main controls
        self.color_history_widget = ColorHistoryWidget(self)
        layout.addWidget(self.color_history_widget)
        
        self.setLayout(layout)
        
        # Load current brush settings
        self.update_from_current_brush()

    def brush_size_to_slider(self, size):
        """Convert brush size (1-1000) to slider value (0-100) with non-linear scaling"""
        if size <= 50:
            # Linear mapping for 1-50: maps to slider 0-70 (70% of slider range)
            return int((size - 1) * 70 / 49)
        else:
            # Linear mapping for 51-1000: maps to slider 71-100 (30% of slider range)
            return int(70 + (size - 50) * 30 / 950)
    
    def slider_to_brush_size(self, slider_value):
        """Convert slider value (0-100) to brush size (1-1000) with non-linear scaling"""
        if slider_value <= 70:
            # Map slider 0-70 to brush size 1-50
            return int(1 + slider_value * 49 / 70)
        else:
            # Map slider 71-100 to brush size 51-1000
            return int(50 + (slider_value - 70) * 950 / 30)
    
    def on_size_slider_changed(self, slider_value):
        """Handle size slider change with non-linear conversion"""
        brush_size = self.slider_to_brush_size(slider_value)
        self.on_size_changed(brush_size)

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
                self.size_slider.setValue(self.brush_size_to_slider(int(size)))
                self.size_value_label.setText(str(int(size)))
                self.current_brush_size = size
            except:
                # Fallback to default if brushSize() doesn't work
                self.size_slider.setValue(self.brush_size_to_slider(10))
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
                self.rotation_widget.setValue(int(rotation))
                self.rotation_value_label.setText(f"{int(rotation)}°")
                self.current_brush_rotation = rotation
            except:
                # Fallback if rotation method doesn't exist
                self.rotation_widget.setValue(0)
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
        # Also force color history update
        if hasattr(self, 'color_history_widget'):
            self.color_history_widget.force_color_update()
    
    def refresh_styles(self):
        """Refresh styles when settings change"""
        style = f"font-size: {BRUSH_ADJUSTMENT_FONT_SIZE};"
        for label in self.findChildren(QLabel):
            if label.text() not in ["Brush Adjustments"]:  # Skip title
                label.setStyleSheet(style)

    def closeEvent(self, event):
        """Clean up timers when widget is closed"""
        if hasattr(self, 'brush_check_timer'):
            self.brush_check_timer.stop()
        if hasattr(self, 'color_history_widget'):
            self.color_history_widget.closeEvent(event)
        super().closeEvent(event)