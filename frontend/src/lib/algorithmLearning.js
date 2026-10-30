import SOURCE from '../../../backend/resources/algorithm-learning.json' with {type:'json'};

export const ALGORITHM_TOPICS = SOURCE.topics;
export const ALGORITHM_TOPIC_BY_ID = Object.fromEntries(ALGORITHM_TOPICS.map(topic=>[topic.id,topic]));
const placements = new Map(ALGORITHM_TOPICS.flatMap(topic=>topic.lectures.map(id=>[id,topic])));
export const lectureDestination = lecture => placements.get(typeof lecture==='string'?lecture:lecture?.id);
export const foundationLectures = entries => entries.filter(item=>!lectureDestination(item));
