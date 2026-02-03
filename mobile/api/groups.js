import { apiClient } from "./client";

export const getGroups = () => apiClient.get("/groups");

export const getOptimizedSettlements = (groupId) =>
  apiClient.post(`/groups/${groupId}/settlements/optimize`, {});

export const createExpense = (groupId, expenseData) =>
  apiClient.post(`/groups/${groupId}/expenses`, expenseData);

export const getGroupDetails = (groupId) => {
  return Promise.all([getGroupMembers(groupId), getGroupExpenses(groupId)]);
};

export const getGroupMembers = (groupId) =>
  apiClient.get(`/groups/${groupId}/members`);

export const getGroupExpenses = (groupId) =>
  apiClient.get(`/groups/${groupId}/expenses`);

export const deleteExpense = (groupId, expenseId) =>
  apiClient.delete(`/groups/${groupId}/expenses/${expenseId}`);

export const createGroup = (name) => apiClient.post("/groups", { name });

export const joinGroup = (joinCode) =>
  apiClient.post("/groups/join", { joinCode });

export const getUserBalanceSummary = () =>
  apiClient.get("/users/me/balance-summary");

export const getFriendsBalance = () =>
  apiClient.get("/users/me/friends-balance");

// New APIs for Group Settings
export const getGroupById = (groupId) => apiClient.get(`/groups/${groupId}`);

export const updateGroup = (groupId, updates) =>
  apiClient.patch(`/groups/${groupId}`, updates);

export const deleteGroup = (groupId) => apiClient.delete(`/groups/${groupId}`);

export const leaveGroup = (groupId) =>
  apiClient.post(`/groups/${groupId}/leave`, {});

export const updateMemberRole = (groupId, memberId, role) =>
  apiClient.patch(`/groups/${groupId}/members/${memberId}`, { role });

export const removeMember = (groupId, memberId) =>
  apiClient.delete(`/groups/${groupId}/members/${memberId}`);
