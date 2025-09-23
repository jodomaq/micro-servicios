import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import Wizard from '../components/Wizard.jsx';
import Result from '../components/Result.jsx';
import './Quiz.css';
import { submitAnswers, getQuestions, createUser } from '../api/api.js';


const Quiz = () => {
  const [currentStep, setCurrentStep] = useState(0);
  const [userAnswers, setUserAnswers] = useState([]);
  const [questionStartTs, setQuestionStartTs] = useState(Date.now());
  const [quizStartTs, setQuizStartTs] = useState(Date.now());
  const [elapsedSec, setElapsedSec] = useState(0);
  const [userId, setUserId] = useState(null);
  const [loading, setLoading] = useState(false);
  const [showResults, setShowResults] = useState(false);
  
  const navigate = useNavigate();
  
  // Preguntas cargadas desde backend
  const [questions, setQuestions] = useState([]);
  
  useEffect(() => {
    const bootstrap = async () => {
      setLoading(true);
      //console.log("Iniciando quiz...");
      try {
        // Crear usuario anónimo (si aún no existe)
        const newUserId = await createUser();
        setUserId(newUserId);
        //console.log("Usuario anónimo creado con ID:", newUserId);
        // Cargar preguntas
        const response = await getQuestions();
        setQuestions(response.data);
        //console.log("Preguntas cargadas:", response.data);
      } catch (error) {
        console.error("Error inicializando el quiz:", error);
      } finally {
        setLoading(false);
      }
    };
    bootstrap();
  }, []);

  // Intervalo para contador global de tiempo transcurrido
  useEffect(() => {
    const id = setInterval(() => {
      setElapsedSec(Math.floor((Date.now() - quizStartTs) / 1000));
    }, 1000);
    return () => clearInterval(id);
  }, [quizStartTs]);

  const formatTime = (total) => {
    const m = Math.floor(total / 60).toString().padStart(2,'0');
    const s = (total % 60).toString().padStart(2,'0');
    return `${m}:${s}`;
  };
  
  const handleAnswer = (answer) => {
    const now = Date.now();
    const time_ms = now - questionStartTs;
    const newAnswers = [...userAnswers, {
      questionId: questions[currentStep].id,
      answer,
      time_ms
    }];
    
    setUserAnswers(newAnswers);
    
    if (currentStep < questions.length - 1) {
      setCurrentStep(currentStep + 1);
      setQuestionStartTs(Date.now());
    } else {
      // Todas las preguntas respondidas
      handleQuizCompletion(newAnswers);
    }
  };
  
  const handleQuizCompletion = async (answers) => {
    if (!userId) {
      console.warn('No userId disponible aún, intentando crear uno...');
      try {
        const newUserId = await createUser();
        setUserId(newUserId);
      } catch (e) {
        console.error('No se pudo crear usuario antes de enviar respuestas', e);
      }
    }
    setLoading(true);
    try {
      // Enviar respuestas al backend. Se envían dentro de un objeto {answers: [...]} según AnswerList
      // y el backend espera user_id como query param. Ajustamos la llamada manualmente usando axios config.
      const payload = { answers };
  const res = await submitAnswers(payload, userId);
      if (res?.data?.user_id) {
        setUserId(res.data.user_id);
      }
      setShowResults(true);
    } catch (error) {
      console.error("Error al enviar respuestas:", error);
      alert('No se pudieron enviar las respuestas. Intenta nuevamente.');
    } finally {
      setLoading(false);
    }
  };
  
  const restart = () => {
    setCurrentStep(0);
    setUserAnswers([]);
    setQuestionStartTs(Date.now());
    setQuizStartTs(Date.now());
    setElapsedSec(0);
    // Mantener el userId existente para no crear múltiples usuarios por sesión
    setShowResults(false);
  };
  
  if (loading) {
    return (
      <div className="quiz-container container">
        <div className="loading">
          <div className="spinner"></div>
          <p>Procesando tus respuestas...</p>
        </div>
      </div>
    );
  }
  
  if (showResults) {
    return (
      <div className="quiz-container container">
        <Result userId={userId} onRestart={restart} />
      </div>
    );
  }
  
  return (
    <div className="quiz-container container">
      <div className="elapsed-timer" style={{textAlign:'right', fontSize:'0.8rem', color:'#555', marginBottom:'4px'}}>
        Tiempo transcurrido: {formatTime(elapsedSec)}
      </div>
      <div className="progress-bar">
        <div 
          className="progress" 
          style={{ width: `${(currentStep / questions.length) * 100}%` }}
        ></div>
        <span className="progress-text">
          Pregunta {currentStep + 1} de {questions.length}
        </span>
      </div>
      
      <div className="quiz-card card">
        {questions.length > 0 && <Wizard 
          question={questions[currentStep]} 
          onAnswer={handleAnswer} 
        />}
        <div className="time-hint" style={{marginTop:'0.75rem', fontSize:'0.75rem', color:'#666'}}>
          Tiempo en esta pregunta: {Math.round((Date.now() - questionStartTs)/1000)}s
        </div>
      </div>
    </div>
  );
};

export default Quiz;