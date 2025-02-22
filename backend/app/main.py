from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from fastapi.middleware.cors import CORSMiddleware
from datetime import datetime, timedelta
from typing import Optional
from pydantic import BaseModel, HttpUrl, Field
import mysql.connector
from .auth import verify_password, get_password_hash, create_access_token
import qrcode
import io
import base64
from PIL import Image, ImageDraw, ImageColor
from jose import JWTError, jwt
from qrcode.image.styles.moduledrawers import RoundedModuleDrawer, CircleModuleDrawer, SquareModuleDrawer, GappedSquareModuleDrawer
from qrcode.image.styles.colormasks import RadialGradiantColorMask, SolidFillColorMask, SquareGradiantColorMask, HorizontalGradiantColorMask, VerticalGradiantColorMask
from qrcode.image.styledpil import StyledPilImage
from qrcode.image.styles.moduledrawers.pil import RoundedModuleDrawer


##### custom rounded eye factory.

import abc
from typing import TYPE_CHECKING, Any, Union
from qrcode.image.styles.colormasks import SolidFillColorMask
from qrcode.image.styles.moduledrawers.pil import HorizontalBarsDrawer, VerticalBarsDrawer
from qrcode.main import QRCode

if TYPE_CHECKING:
    from qrcode.image.base import BaseImage
    from qrcode.main import ActiveWithNeighbors, QRCode


class BaseEyeDrawer(abc.ABC):
    needs_processing = True
    needs_neighbors = False
    factory: "StyledPilImage2"

    def initialize(self, img: "BaseImage") -> None:
        self.img = img

    def draw(self):
        (nw_eye_top, _), (_, nw_eye_bottom) = (
            self.factory.pixel_box(0, 0),
            self.factory.pixel_box(6, 6),
        )
        (nw_eyeball_top, _), (_, nw_eyeball_bottom) = (
            self.factory.pixel_box(2, 2),
            self.factory.pixel_box(4, 4),
        )
        self.draw_nw_eye((nw_eye_top, nw_eye_bottom))
        self.draw_nw_eyeball((nw_eyeball_top, nw_eyeball_bottom))

        (ne_eye_top, _), (_, ne_eye_bottom) = (
            self.factory.pixel_box(0, self.factory.width - 7),
            self.factory.pixel_box(6, self.factory.width - 1),
        )
        (ne_eyeball_top, _), (_, ne_eyeball_bottom) = (
            self.factory.pixel_box(2, self.factory.width - 5),
            self.factory.pixel_box(4, self.factory.width - 3),
        )
        self.draw_ne_eye((ne_eye_top, ne_eye_bottom))
        self.draw_ne_eyeball((ne_eyeball_top, ne_eyeball_bottom))

        (sw_eye_top, _), (_, sw_eye_bottom) = (
            self.factory.pixel_box(self.factory.width - 7, 0),
            self.factory.pixel_box(self.factory.width - 1, 6),
        )
        (sw_eyeball_top, _), (_, sw_eyeball_bottom) = (
            self.factory.pixel_box(self.factory.width - 5, 2),
            self.factory.pixel_box(self.factory.width - 3, 4),
        )
        self.draw_sw_eye((sw_eye_top, sw_eye_bottom))
        self.draw_sw_eyeball((sw_eyeball_top, sw_eyeball_bottom))

    @abc.abstractmethod
    def draw_nw_eye(self, position): ...

    @abc.abstractmethod
    def draw_nw_eyeball(self, position): ...

    @abc.abstractmethod
    def draw_ne_eye(self, position): ...

    @abc.abstractmethod
    def draw_ne_eyeball(self, position): ...

    @abc.abstractmethod
    def draw_sw_eye(self, position): ...

    @abc.abstractmethod
    def draw_sw_eyeball(self, position): ...


class CustomEyeDrawer(BaseEyeDrawer):
    def draw_nw_eye(self, position):
        draw = ImageDraw.Draw(self.img)
        draw.rounded_rectangle(
            position,
            fill=None,
            width=self.factory.box_size,
            outline="black",
            radius=self.factory.box_size * 2,
            corners=[True, True, True, True],
        )

    def draw_nw_eyeball(self, position):
        draw = ImageDraw.Draw(self.img)
        draw.rounded_rectangle(
            position,
            fill=True,
            outline="black",
            radius=self.factory.box_size,
            corners=[True, True, True, True],
        )

    def draw_ne_eye(self, position):
        draw = ImageDraw.Draw(self.img)
        draw.rounded_rectangle(
            position,
            fill=None,
            width=self.factory.box_size,
            outline="black",
            radius=self.factory.box_size * 2,
            corners=[True, True, True, True],
        )

    def draw_ne_eyeball(self, position):
        draw = ImageDraw.Draw(self.img)
        draw.rounded_rectangle(
            position,
            fill=True,
            outline="black",
            radius=self.factory.box_size,
            corners=[True, True, True, True],
        )

    def draw_sw_eye(self, position):
        draw = ImageDraw.Draw(self.img)
        draw.rounded_rectangle(
            position,
            fill=None,
            width=self.factory.box_size,
            outline="black",
            radius=self.factory.box_size * 2,
            corners=[True, True, True, True],
        )

    def draw_sw_eyeball(self, position):
        draw = ImageDraw.Draw(self.img)
        draw.rounded_rectangle(
            position,
            fill=True,
            outline="black",
            radius=self.factory.box_size,
            corners=[True, True, True, True],
        )


class StyledPilImage2(StyledPilImage):
    def drawrect_context(self, row: int, col: int, qr: QRCode[Any]):
        box = self.pixel_box(row, col)
        if self.is_eye(row, col):
            drawer = self.eye_drawer
            if getattr(self.eye_drawer, "needs_processing", False):
                return
        else:
            drawer = self.module_drawer

        is_active: Union[bool, ActiveWithNeighbors] = (
            qr.active_with_neighbors(row, col)
            if drawer.needs_neighbors
            else bool(qr.modules[row][col])
        )

        drawer.drawrect(box, is_active)

    def process(self) -> None:
        if getattr(self.eye_drawer, "needs_processing", False):
            self.eye_drawer.factory = self
            self.eye_drawer.draw()
        super().process()








import logging

class RoundedEyeDrawer(RoundedModuleDrawer):
    def draw(self, box, image, fill_color):
        """
        Draw a rounded rectangle for the QR eye using the given box dimensions.
        This overrides the default square drawing.
        """
        draw = ImageDraw.Draw(image)
        # Calculate a suitable radius based on the box size
        radius = (box[2] - box[0]) // 4  # adjust this fraction as needed
        draw.rounded_rectangle(box, radius=radius, fill=fill_color)


# Constants for JWT
SECRET_KEY = "your-secret-key-here"  # In production, use a secure secret key an put them in environment variables
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

# OAuth2 scheme for token handling
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

# Function to decode and verify JWT token
async def get_current_user(token: str = Depends(oauth2_scheme)):
    """
    Verify and decode JWT token to get current user
    Args:
        token: JWT token from request
    Returns:
        username: String containing the username from token
    Raises:
        HTTPException: If token is invalid or expired
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        # Decode JWT token
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
        return username
    except JWTError:
        raise credentials_exception

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Adjust this for security in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/api/hello")
def read_root():
    return {"message": "Hello from FastAPI!"}

@app.get("/api/time")
def read_root():
    return {"time": datetime.now().isoformat()}

class EchoRequest(BaseModel):
    text: str
    number: int

@app.post("/api/echo")
def echo(request: EchoRequest):
    return {"message": request.text, "number": request.number}

# Database connection
def get_db():
    db = mysql.connector.connect(
        host="database",
        user="myuser",
        password="mypassword",
        database="myapp"
    )
    try:
        yield db
    finally:
        db.close()

class UserCreate(BaseModel):
    username: str
    email: str
    password: str

class Token(BaseModel):
    access_token: str
    token_type: str

# Set up logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Function to convert hex color to RGB tuple
def hex_to_rgb(hex_color: str) -> tuple:
    """Convert hex color string to RGB tuple"""
    # Remove the '#' if present
    hex_color = hex_color.lstrip('#')
    # Convert hex to RGB
    return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))

# Define the QRCodeOptions model
class QRCodeOptions(BaseModel):
    """
    Pydantic model for QR code generation options
    
    Attributes:
        url (str): The URL to encode in the QR code
        dot_style (str): Style of QR code dots (square, rounded, circle, gapped)
        fill_color (str): Hex color code for QR code foreground
        back_color (str): Hex color code for QR code background
        eye_style (str): Style of QR code eyes (square, rounded, circle, gapped)
    """
    url: str
    dot_style: str = Field("square", pattern="^(square|rounded|circle|gapped|horizontal|vertical)$")
    fill_color: str = Field(..., pattern="^#[0-9A-Fa-f]{6}$")
    back_color: str = Field(..., pattern="^#[0-9A-Fa-f]{6}$")
    eye_style: str = Field("square", pattern="^(square|rounded|circle|gapped|custom)$")

@app.post("/api/signup", response_model=Token)
async def signup(user: UserCreate, db: mysql.connector.MySQLConnection = Depends(get_db)):
    cursor = db.cursor(dictionary=True)
    
    # Check if username is already taken in the database
    cursor.execute("SELECT username FROM users WHERE username = %s", (user.username,))
    if cursor.fetchone():
        raise HTTPException(
            status_code=400,
            detail="This username is already taken"
        )
    
    # Check if email is already registered in the database
    cursor.execute("SELECT email FROM users WHERE email = %s", (user.email,))
    if cursor.fetchone():
        raise HTTPException(
            status_code=400,
            detail="An account with this email already exists"
        )
    
    # If both checks pass, create new user with hashed password
    try:
        hashed_password = get_password_hash(user.password)
        cursor.execute(
            "INSERT INTO users (username, email, password_hash) VALUES (%s, %s, %s)",
            (user.username, user.email, hashed_password)
        )
        db.commit()
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail="Failed to create account. Please try again."
        )
    
    # Generate JWT token for the new user
    access_token = create_access_token(
        data={"sub": user.username},
        expires_delta=timedelta(minutes=30)
    )
    return {"access_token": access_token, "token_type": "bearer"}

@app.post("/api/login", response_model=Token)
async def login(form_data: OAuth2PasswordRequestForm = Depends(), db: mysql.connector.MySQLConnection = Depends(get_db)):
    cursor = db.cursor(dictionary=True)
    
    # Check if user exists in database
    cursor.execute(
        "SELECT * FROM users WHERE username = %s",
        (form_data.username,)
    )
    user = cursor.fetchone()
    
    # Return error if username not found
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Username not found",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Verify password against stored hash
    if not verify_password(form_data.password, user["password_hash"]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Generate JWT token for successful login
    access_token = create_access_token(
        data={"sub": user["username"]},
        expires_delta=timedelta(minutes=30)
    )
    return {"access_token": access_token, "token_type": "bearer"}

# Added helper function to generate QR code image as base64. This function implements the QR drawing logic.
def generate_qr_image(options: QRCodeOptions) -> str:
    # Convert hex colors to RGB tuples
    fill_color_rgb = hex_to_rgb(options.fill_color)
    back_color_rgb = hex_to_rgb(options.back_color)
    logger.debug(f"Converted colors - Fill: {fill_color_rgb}, Back: {back_color_rgb}")

    # Create and configure QR code
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=10,
        border=4,
    )
    qr.add_data(options.url)
    qr.make(fit=True)

    # Style configuration mapping for modules (dots)
    style_mapping = {
        "square": SquareModuleDrawer(),
        "rounded": RoundedModuleDrawer(),
        "circle": CircleModuleDrawer(),
        "gapped": GappedSquareModuleDrawer(),
        "horizontal": HorizontalBarsDrawer(),
        "vertical": VerticalBarsDrawer(),
    }
    module_drawer = style_mapping.get(options.dot_style)

    eye_style_mapping = {
        "square": SquareModuleDrawer(),
        "rounded": RoundedModuleDrawer(),
        "circle": CircleModuleDrawer(),
        "gapped": GappedSquareModuleDrawer(),
        "custom": CustomEyeDrawer(),
    }
    eye_drawer = eye_style_mapping.get(options.eye_style)

    if not module_drawer or not eye_drawer:
        logger.error(f"Invalid style - Dot: {options.dot_style}, Eye: {options.eye_style}")
        raise HTTPException(status_code=400, detail="Invalid style options")

    logger.debug(f"Using styles - Module: {type(module_drawer).__name__}, Eye: {type(eye_drawer).__name__}")

    # Generate the QR code image with styling
    try:
        qr_image = qr.make_image(
            image_factory=StyledPilImage2,
            module_drawer=module_drawer,
            eye_drawer=eye_drawer,
            color_mask=SolidFillColorMask(
                front_color=fill_color_rgb,
                back_color=back_color_rgb
            )
        )
    except Exception as img_error:
        logger.error(f"QR generation error: {str(img_error)}")
        raise HTTPException(status_code=500, detail="QR generation failed")

    # Convert QR image to base64 string
    try:
        buffered = io.BytesIO()
        qr_image.save(buffered, format="PNG")
        qr_base64 = base64.b64encode(buffered.getvalue()).decode()
    except Exception as conv_error:
        logger.error(f"Base64 conversion failed: {str(conv_error)}")
        raise HTTPException(status_code=500, detail="Failed to convert QR image")

    return qr_base64

# Endpoint to generate QR code without saving to the database
@app.post("/api/qr/create")
async def generate_qr(
    options: QRCodeOptions,
    current_user: str = Depends(get_current_user)
):
    # Note: This endpoint only returns the generated QR code.
    qr_base64 = generate_qr_image(options)
    return {
        "qr_code": f"data:image/png;base64,{qr_base64}",
        "url": options.url
    }

# New endpoint to save the generated QR code to the database
@app.post("/api/qr/save")
async def save_qr(
    options: QRCodeOptions,
    current_user: str = Depends(get_current_user),
    db: mysql.connector.MySQLConnection = Depends(get_db)
):
    # Generate QR code using the same logic
    qr_base64 = generate_qr_image(options)
    
    # Database operations to save QR code only when explicitly requested
    try:
        cursor = db.cursor(dictionary=True)
        cursor.execute("SELECT id FROM users WHERE username = %s", (current_user,))
        user = cursor.fetchone()

        if not user:
            logger.error(f"User not found: {current_user}")
            raise HTTPException(status_code=404, detail="User not found")
        
        # Save QR code data to the database
        cursor.execute(
            """INSERT INTO qr_codes 
               (user_id, qr_data, dot_style, fill_color, back_color, qr_image, eye_style) 
               VALUES (%s, %s, %s, %s, %s, %s, %s)""",
            (user['id'], options.url, options.dot_style, options.fill_color, options.back_color, qr_base64, options.eye_style)
        )
        db.commit()
        logger.debug("QR code saved to database successfully")
    except Exception as db_error:
        logger.error(f"Database operation failed: {str(db_error)}")
        raise HTTPException(status_code=500, detail="Database operation failed")

    return {
        "qr_code": f"data:image/png;base64,{qr_base64}",
        "url": options.url,
        "message": "QR code saved successfully"
    }

@app.get("/api/qr")
async def get_user_qr_codes(current_user: str = Depends(get_current_user), db: mysql.connector.MySQLConnection = Depends(get_db)):
    try:
        cursor = db.cursor(dictionary=True)
        
        # Get user_id from username
        cursor.execute("SELECT id FROM users WHERE username = %s", (current_user,))
        user = cursor.fetchone()
        
        # Get all QR codes for the user with pre-generated images
        cursor.execute("""
            SELECT id, qr_data as url, dot_style, fill_color, back_color, qr_image, created_at
            FROM qr_codes 
            WHERE user_id = %s 
            ORDER BY created_at DESC
        """, (user['id'],))
        
        qr_codes = cursor.fetchall()
        
        # Directly return the QR codes with pre-generated images
        return qr_codes
        
    except Exception as e:
        logging.error(f"Error retrieving QR codes: {str(e)}")  # Error log
        raise HTTPException(
            status_code=500,
            detail=str(e)
        )

@app.delete("/api/qr/{qr_id}")
async def delete_qr_code(
    qr_id: int, 
    current_user: str = Depends(get_current_user), 
    db: mysql.connector.MySQLConnection = Depends(get_db)
):
    try:
        cursor = db.cursor(dictionary=True)
        
        # Get user_id from username
        cursor.execute("SELECT id FROM users WHERE username = %s", (current_user,))
        user = cursor.fetchone()
        
        # Check if QR code exists and belongs to the user
        cursor.execute("""
            SELECT id FROM qr_codes 
            WHERE id = %s AND user_id = %s
        """, (qr_id, user['id']))
        
        qr_code = cursor.fetchone()
        if not qr_code:
            raise HTTPException(
                status_code=404,
                detail="QR code not found or you don't have permission to delete it"
            )
        
        # Delete the QR code
        cursor.execute("DELETE FROM qr_codes WHERE id = %s", (qr_id,))
        db.commit()
        
        return {"message": "QR code deleted successfully"}
        
    except HTTPException as he:
        raise he
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=str(e)
        )

