
from langchain_core.output_parsers import PydanticOutputParser
from src.models.question_schemas import MCQQuestion,FillBlankQuestion
from src.prompts.templates import mcq_prompt_template,fill_blank_prompt_template
from src.llm.groq_client import get_groq_llm
from src.config.settings import settings
from src.common.logger import get_logger
from src.common.custom_exception import CustomException


class QuestionGenerator:
    def __init__(self):
        self.llm = get_groq_llm()
        self.logger = get_logger(self.__class__.__name__)

    def _retry_and_parse(self,prompt,parser,topic,difficulty):

        for attempt in range(settings.MAX_RETRIES):
            try:
                self.logger.info(f"Generating question for topic {topic} with difficulty {difficulty}")

                response = self.llm.invoke(prompt.format(topic=topic , difficulty=difficulty))

                parsed = parser.parse(response.content)

                self.logger.info("Successfully parsed the question")

                return parsed
            
            except Exception as e:
                self.logger.error(f"Error coming : {str(e)}")
                if attempt==settings.MAX_RETRIES-1:
                    raise CustomException(f"Generation failed after {settings.MAX_RETRIES} attempts", e)
                
    def generate_mcq(self, topic: str, difficulty: str = 'medium') -> MCQQuestion:
        try:
            parser = PydanticOutputParser(pydantic_object=MCQQuestion)

            question = self._retry_and_parse(mcq_prompt_template, parser, topic, difficulty)

            # 1. Normalize options and correct_answer to prevent whitespace errors
            options = [opt.strip() for opt in question.options]
            correct_answer = question.correct_answer.strip()
        
            # Update the object with cleaned strings
            question.options = options
            question.correct_answer = correct_answer

            # 2. Strict validation check
            is_valid_length = len(options) == 4
            is_answer_in_options = correct_answer in options

            if not is_valid_length or not is_answer_in_options:
            # Enhanced error message for debugging
                error_details = f"Options: {len(options)}, Match Found: {is_answer_in_options}"
            self.logger.warning(f"Validation failed: {error_details}. Raw: {question}")
            raise ValueError(f"Invalid MCQ Structure ({error_details})")
        
            self.logger.info("Generated a valid MCQ Question")
            return question
    
        except Exception as e:
            self.logger.error(f"Failed to generate MCQ : {str(e)}")
            raise CustomException("MCQ generation failed", e) 
    
    def generate_fill_blank(self,topic:str,difficulty:str='medium') -> FillBlankQuestion:
        try:
            parser = PydanticOutputParser(pydantic_object=FillBlankQuestion)

            question = self._retry_and_parse(fill_blank_prompt_template,parser,topic,difficulty)

            if "___" not in question.question:
                raise ValueError("Fill in blanks should contain '___'")
            
            self.logger.info("Generated a valid Fill in Blanks Question")
            return question
        
        except Exception as e:
            self.logger.error(f"Failed to generate fillups : {str(e)}")
            raise CustomException("Fill in blanks generation failed" , e)

