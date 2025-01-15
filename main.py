from fastapi import FastAPI, File, UploadFile, Query
from openai import OpenAI
import base64
from dotenv import load_dotenv
import os
from starlette.responses import JSONResponse
import json

# Load environment variables from the .env file
load_dotenv()

# Initialize OpenAI client with the API key from the environment
client = OpenAI()

# Initialize FastAPI app
app = FastAPI(
    title="Food Image Analysis API",
    description="API to analyze food images and provide detailed nutritional information in the specified language.",
    version="1.0.0",
    contact={
        "name": "Your Name",
        "email": "your_email@example.com",
    },
)

# Endpoint to analyze food image
@app.post(
    "/analyze-food-image",
    summary="Analyze a food image",
    description="Upload a food image to get its analysis, including meal details, quantity, and nutritional breakdown in the specified language.",
    tags=["Food Analysis"]
)
async def analyze_food_image(
    file: UploadFile = File(..., description="The image file of the food to be analyzed."),
    language: str = Query(
        "en",
        description="The language in which the analysis should be returned (e.g., 'en' for English, 'fr' for French)."
    )
):
    """
    Analyze a food image to extract information about the meal and its nutritional properties.

    - **file**: Upload an image of the food.
    - **language**: Specify the language for the response. Defaults to English (`en`).
    """
    # Read the uploaded file
    file_content = await file.read()
    
    # Encode the file to base64
    base64_image = base64.b64encode(file_content).decode("utf-8")
    
    # Send the image to OpenAI API
    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You are a food analysis assistant. Always respond with a **valid JSON object** "
                        "that adheres to this schema:\n\n"
                        "{\n"
                        "    \"mealDetails\": {\n"
                        "        \"estimatedMealName\": \"<string>\",\n"
                        "        \"description\": \"<string>\"\n"
                        "    },\n"
                        "    \"quantity\": {\n"
                        "        \"estimatedWeight\": \"<string>\"\n"
                        "    },\n"
                        "    \"nutritionalAnalysis\": {\n"
                        "        \"calories\": \"<string>\",\n"
                        "        \"macronutrients\": {\n"
                        "            \"proteins\": \"<string>\",\n"
                        "            \"carbohydrates\": \"<string>\",\n"
                        "            \"fats\": \"<string>\"\n"
                        "        },\n"
                        "        \"vitamins\": {\n"
                        "            \"<vitaminName>\": \"<string>\"\n"
                        "        },\n"
                        "        \"minerals\": {\n"
                        "            \"<mineralName>\": \"<string>\"\n"
                        "        },\n"
                        "        \"otherNutritionalInformation\": {\n"
                        "            \"<key>\": \"<value>\"\n"
                        "        }\n"
                        "    }\n"
                        "}\n\n"
                        "Respond with nothing else but the JSON object. "
                        
                    )
                },
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": (
                                f"Analyze this food image. Respond in {language}. Predict the meal name, estimate its "
                                "quantity (in grams), and provide a detailed nutrition analysis including calories, "
                                "proteins, carbs, fats, vitamins, and minerals."
                            )
                        },
                        {
                            "type": "image_url",
                            "image_url": {"url": f"data:image/jpeg;base64,{base64_image}"},
                        },
                    ],
                }
            ],
            max_tokens=300,
        )
        
        # Extract the response content
        result = response.choices[0].message.content
        print(response)

        # Validate and parse the JSON response
        try:
            parsed_result = json.loads(result)
        except json.JSONDecodeError:
            return JSONResponse(content={"error": "Invalid JSON response from the AI model."}, status_code=500)

        return {"analysis": parsed_result}

    except Exception as e:
        return JSONResponse(content={"error": str(e)}, status_code=500)
