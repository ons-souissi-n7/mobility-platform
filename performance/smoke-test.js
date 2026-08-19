import http from 'k6/http';
import { check, sleep } from 'k6';

export const options = {
  vus: 5,
  duration: '30s',
};

export default function () {
  const response = http.get('http://host.docker.internal:8000/health/');

  check(response, {
    'status is 200': (r) => r.status === 200,
    'response time < 500 ms': (r) => r.timings.duration < 500,
  });   

  sleep(1);
}