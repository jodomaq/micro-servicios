import axios from 'axios';

// Base de la API configurable por entorno.
// Dev:  VITE_API_BASE=/api (proxy en vite)
// Prod: VITE_API_BASE=/iqtest/api (resuelto por nginx en subruta)
const apiBase = (import.meta.env.VITE_API_BASE || '/iqtest/api').replace(/\/$/, '');

// Configuración base de axios (rutas relativas para permitir dominios dinámicos)
const api = axios.create({
  baseURL: apiBase,
  headers: {
    'Content-Type': 'application/json'
  }
});

/**
 * Envía las respuestas del usuario al backend
 * @param {Array} answers - Array de objetos con questionId y answer
 * @returns {Promise} - Promesa con la respuesta del servidor
 */
export const submitAnswers = (answersPayload, userId) => {
  // answersPayload: {answers: Array<{questionId:number, answer:string}>}
  // backend definió endpoint /submit-answers/ que acepta AnswerList y user_id query param
  const config = {};
  if (userId) {
    config.params = { user_id: userId };
  }
  return api.post('/submit-answers/', answersPayload, config);
};

/**
 * Crea un usuario anónimo y devuelve su ID
 * @returns {Promise<number>} user_id
 */
export const createUser = async () => {
  const res = await api.post('/users/');
  return res.data.user_id;
};

/**
 * Actualiza nombre/email del usuario
 * @param {number} userId
 * @param {{name?:string,email?:string}} data
 */
export const updateUser = async (userId, data) => {
  const res = await api.patch(`/users/${userId}`, data);
  return res.data;
};

/**
 * Verifica un pago con PayPal
 * @param {Object} paymentData - Datos del pago (orderId, userId)
 * @returns {Promise} - Promesa con la respuesta del servidor
 */
export const verifyPayment = (paymentData) => {
  return api.post('/paypal/verify/', paymentData);
};

/**
 * Crea una orden de PayPal
 * @param {Object} cartData - Datos del carrito
 * @returns {Promise} - Promesa con la orden creada
 */
export const createPayPalOrder = (cartData) => {
  return fetch(`${apiBase}/orders`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(cartData),
  }).then(res => {
    if (!res.ok) return res.json().then(json => Promise.reject(json));
    return res.json();
  });
};

/**
 * Captura una orden de PayPal
 * @param {String} orderId - ID de la orden a capturar
 * @returns {Promise} - Promesa con los detalles de la captura
 */
export const capturePayPalOrder = (orderId) => {
  return fetch(`${apiBase}/orders/${orderId}/capture`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
  }).then(res => {
    if (!res.ok) return res.json().then(json => Promise.reject(json));
    return res.json();
  });
};

/**
 * Solicita la evaluación de las respuestas del usuario
 * @param {Number} userId - ID del usuario
 * @returns {Promise} - Promesa con los resultados de la evaluación
 */
export const evaluate = (userId) => {
  return api.post(`/evaluate/${userId}`);
};

/**
 * Obtiene preguntas del test
 * @returns {Promise} - Promesa con las preguntas del test
 */
export const getQuestions = () => {
  return api.get('/questions/');
};

/**
 * Obtiene un resultado específico
 * @param {Number} resultId - ID del resultado
 * @returns {Promise} - Promesa con el resultado
 */
export const getResult = (resultId) => {
  return api.get(`/results/${resultId}/`);
};

export default {
  submitAnswers,
  verifyPayment,
  createPayPalOrder,
  capturePayPalOrder,
  evaluate,
  getQuestions,
  getResult
};
