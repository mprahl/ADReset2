/* eslint-disable class-methods-use-this */
import AuthService from './AuthService';


class APIService {
  constructor(apiURL) {
    this.apiURL = apiURL || 'http://127.0.0.1:5000/api/v1/';
    this.authService = new AuthService(apiURL);
  }

  getSecretQuestions() {
    return this.authService.authenticatedAPICall('questions');
  }

  addSecretQuestion(question) {
    return this.authService.authenticatedAPICall('questions', { question }, 'post', 'admin');
  }

  patchSecretQuestion(questionID, data) {
    return this.authService.authenticatedAPICall(`questions/${questionID}`, data, 'patch', 'admin');
  }
}


export default APIService;
