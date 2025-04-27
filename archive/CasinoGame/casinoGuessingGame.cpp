#include <iostream>
#include <string> 
#include <cstdlib> // for random numbers
#include <ctime>

using namespace std;

void rules();
void game();

int main()
{
    string playerName;
    int balance;          // player's balance
    int bettingAmount;
    int guess;
    int dice;             // stores the random number
    char choice;
    char addMoney;
    srand(time(0));       // "Seed" the random generator
    cout << "\n\t\t======== WELCOME TO CASINO NUMBER GUESSING =======\n";
    cout << "\n\nWhat's your Name: ";
    getline(cin, playerName);
    cout << "\n" << playerName << ", please enter the starting balance to play game: $";
    cin >> balance;

    do
    {
      system("clear"); // system("cls") if on Windows
      rules();
      cout << "\n\nYour current balance is $" << balance << "\n\n";

      // Get player's betting balance
      do
      {
        cout << "Hey " << playerName <<", enter amount to bet : $";
        cin >> bettingAmount;
        if(bettingAmount > balance)
          cout << "\nBetting amount can't be more than current balance!\n"
          << "\nRe-enter balance\n";
      }while(bettingAmount > balance);

        // Get player's numbers
      do
      {
        cout << "\nGuess any betting number between 1 & 10 : ";
        cin >> guess;
        if(guess <= 0 || guess > 10)
          cout << "\nNumber should be between 1 to 10!\n";
      }while(guess <= 0 || guess > 10);

      dice = rand()%10 + 1;

      if(dice == guess)
      {
        cout << "\n\nYou are in luck!! You have won $" << bettingAmount * 10;
        balance = balance + bettingAmount * 10;
      }
      else
      {
        cout << "\nOops, better luck next time! You lost $"<< bettingAmount;
        balance = balance - bettingAmount;
      }

      cout << "\nThe winning number was: " << dice;
      cout << "\n" << playerName <<", You have a balance of $" << balance;

      if(balance == 0)
      {
        cout << "\nYou have no money to play.\n\nDo you want to add more money to your balance? (y/n) ";
        cin >> addMoney;
        if(addMoney == 'Y' || addMoney == 'y')
        {
          cout << "\nHow much money did you want to add? $";
          cin >> balance;
        }
        else
        {
          break;
        }
      }

      cout << "\n\n-->Do you want to play again (y/n)? ";
      cin >> choice;

    }while(choice =='Y'|| choice=='y');

    cout << "\n\nThanks for playing the game. Your balance is $" << balance << "\n\n";

    return 0;
}

void rules()
{
  // system("cls"); // for Windows
  system("clear");  // for Linux systems
  cout << "\t\t====== CASINO NUMBER GUESSING RULES! ======\n\n";
  cout << "\t1. Choose a number between 1 to 10.\n";
  cout << "\t2. Winner gets 10 times of the money bet.\n";
  cout << "\t3. Wrong bet, and you lose the amount you bet.\n\n";
}

