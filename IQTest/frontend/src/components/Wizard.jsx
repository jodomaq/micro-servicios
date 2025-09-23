import React, { useState, useEffect } from 'react';
import { getQuestions } from '../api/api';
import './Wizard.css';

export default function Wizard({ onAnswer, question }) {
  const [selectedOption, setSelectedOption] = useState(null);

  const handleOptionSelect = (option) => {
    setSelectedOption(option);
  };

  const handleNext = () => {
    if (selectedOption) {
      onAnswer(selectedOption);
      setSelectedOption(null);
    }
  };

  return (
    <div className="wizard">
      <h2 className="question">{question.text}</h2>
      
      <div className="options">
        {question.options.map((option, index) => (
          <div 
            key={index}
            className={`option ${selectedOption === option ? 'selected' : ''}`}
            onClick={() => handleOptionSelect(option)}
          >
            <span className="option-letter">{String.fromCharCode(65 + index)}</span>
            <span className="option-text">{option}</span>
          </div>
        ))}
      </div>
      
      <button 
        className="btn btn-primary next-btn"
        disabled={!selectedOption}
        onClick={handleNext}
      >
        Siguiente
      </button>
    </div>
  );
}