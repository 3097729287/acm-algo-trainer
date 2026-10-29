// Entry position is navigation state. Reset it without erasing learning facts,
// completed checks, experimental drafts or guided-problem work.
export function startCourseAtBeginning(preferences,course){
 if(!course?.id||!course.first)return preferences;
 const paths=preferences.learningPaths||{},saved=paths[course.id]||{};
 if(paths.activePath===course.id&&saved.mode==='learn'&&saved.labV1?.chapter===course.first)return preferences;
 return {...preferences,learningPaths:{...paths,activePath:course.id,[course.id]:{...saved,mode:'learn',labV1:{...saved.labV1,chapter:course.first}}}};
}

// A menu is a concise outline. Keep the original title for the actual lesson.
export function chapterMenuTitle(chapter){
 if(typeof chapter?.shortTitle==='string'&&chapter.shortTitle.trim())return chapter.shortTitle.trim();
 const title=typeof chapter==='string'?chapter:typeof chapter?.title==='string'?chapter.title:'';
 return title.split('：',1)[0].trim()||title.trim();
}
