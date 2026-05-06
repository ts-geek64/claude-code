export interface Profile {
  id: string;
  name: string;
  email: string;
}

export interface UpdateProfilePayload {
  name: string;
}

export interface UpdateProfileResponse {
  profile: Profile;
}
