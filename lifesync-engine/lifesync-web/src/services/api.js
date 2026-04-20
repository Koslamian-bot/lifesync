// src/services/api.js

export const fetchTwoWeekPlan = async () => {
  return new Promise((resolve) => {
    setTimeout(() => {
      resolve({
        plan_title: "Peak Productivity Plan v2.4",
        sprint_start: "2026-04-14",
        sprint_end: "2026-04-27",
        milestones: [
          { goal_name: "Master AI Engineering", week_1_target: "Complete RAG basics", week_2_target: "Deploy vector DB" },
          { goal_name: "Learn Spanish", week_1_target: "Present tense verbs", week_2_target: "Have a 5 min conversation" }
        ],
        daily_plans: [
          {
            date: "2026-04-14",
            day_name: "Tuesday",
            week_number: 1,
            day_summary: "A strong start focusing on core engineering skills and physical health.",
            tasks: [
              {
                time_start: "07:30",
                time_end: "08:45",
                task_name: "Hypertrophy: Chest",
                category: "goal",
                goal_ref: "Fitness",
                notes: "Morning strength block.",
                exercises: [
                  { name: "Barbell Bench Press", sets: 4, reps: "8", notes: "185 lbs" },
                  { name: "Incline Dumbbell Flyes", sets: 3, reps: "12", notes: "45 lbs" }
                ]
              },
              {
                time_start: "09:00",
                time_end: "11:30",
                task_name: "Deep Work: Project Aurora",
                category: "rigid",
                goal_ref: null,
                notes: "Core work hours."
              }
            ]
          }
        ],
        general_advice: "Focus on consistency over intensity in Week 1."
      });
    }, 800);
  });
};