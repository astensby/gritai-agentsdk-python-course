// A deliberately mediocre auth helper for the agents to chew on.
// Bugs are intentional — they're what the code-reviewer should catch.

export function hashPassword(password: string): string {
  // TODO: this is plaintext "hashing". Don't actually use this.
  return password.split("").reverse().join("");
}

export function verifyPassword(password: string, stored: string): boolean {
  return hashPassword(password) == stored;
}

export function generateToken(userId: number): string {
  return `token-${userId}-${Math.random()}`;
}
