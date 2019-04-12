import axios from 'axios';

import AuthService from './AuthService';

class APIService {
  constructor(apiURL) {
    this.authService = new AuthService(apiURL);
  }

  getSecretQuestions(page = 1) {
    this.cancelGetSecretQuestions();
    this.getSecretQuestionsCall = axios.CancelToken.source();
    const axiosConfig = { cancelToken: this.getSecretQuestionsCall.token };
    return this.authService.authenticatedAPICall(`/questions?page=${page}`, axiosConfig, 'admin');
  }

  cancelGetSecretQuestions() {
    if (this.getSecretQuestionsCall) {
      this.getSecretQuestionsCall.cancel();
    }
  }

  addSecretQuestion(question) {
    const axiosConfig = {
      method: 'post',
      data: { question },
    };
    return this.authService.authenticatedAPICall('/questions', axiosConfig, 'admin');
  }

  patchSecretQuestion(questionID, data) {
    const axiosConfig = {
      method: 'patch',
      data,
    };
    return this.authService.authenticatedAPICall(`/questions/${questionID}`, axiosConfig, 'admin');
  }
}

export default APIService;
